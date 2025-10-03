import logging
import os
import pprint as pp
from collections import defaultdict
from datetime import datetime as dt
from django.core.management.base import BaseCommand
from catstats.models import BibRecord, Field962, RepeatableSubfield
from alma_api_client import AlmaAnalyticsClient, APIError

logger = logging.getLogger(__name__)


def get_filter(yyyymm):
    # By year/month: quick enough, usually 5000-10000 rows
    # No need for LOWER with just digits
    filter_xml = f"""
<sawx:expr xsi:type="sawx:list" op="like"
    xmlns:saw="com.siebel.analytics.web/report/v1.1"
    xmlns:sawx="com.siebel.analytics.web/expression/v1.1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
>
    <sawx:expr xsi:type="sawx:sqlExpression">"Bibliographic Details"."Local Param 02"</sawx:expr>
    <sawx:expr xsi:type="xsd:string">%$$c {yyyymm}%</sawx:expr>
</sawx:expr>
"""
    # Strip out formatting characters which make API unhappy
    return filter_xml.replace("\n", "").replace("\t", "")


def run_report(filter):
    logger.info(f"Running with {filter=}....")
    api_key = os.getenv("ALMA_API_KEY")
    alma_client = AlmaAnalyticsClient(api_key)
    report_path = (
        "/shared/University of California Los Angeles (UCLA) 01UCS_LAL/Cataloging"
        "/Reports/API/Cataloging Statistics (API)"
    )

    filter_xml = get_filter(filter)

    alma_client.set_report_path(report_path)
    alma_client.set_filter_xml(filter_xml)

    try:
        report = alma_client.get_report()
    except APIError as ex:
        logger.error(f"APIError on initial get_report(): {ex}")
        raise

    return report


def add_data_to_db(report_data):
    logger.info(f"{len(report_data)=}")
    replaced_bibs = 0
    for row in report_data:
        # Each row is one bib, with 1+ 962 fields embeded in 'Local Param 02'.
        mmsid = row["MMS Id"]
        # Remove existing bib (and all field/subfield children)
        if BibRecord.objects.filter(mmsid=mmsid).exists():
            replaced_bibs += 1
            BibRecord.objects.filter(mmsid=mmsid).delete()

        # TODO: Is this TRY needed? If so, improve the exception processing
        try:
            # First save the bib-level data
            bib = BibRecord.objects.create(
                mmsid=mmsid,
                language_code=row.get("Language Code", ""),
                place_code=row.get("Place Code", ""),
                material_type=row.get("Material Type", ""),
                resource_type=row.get("Resource Type", ""),
            )
            # Split rows where Local Param 02 contains multiple 962 fields, delimited by ';'
            for fld_962 in row["962 - Local Param 02"].split(";"):
                r = fld_962.strip()
                # Creates dict of lists, which is a pain
                sfd_dict = defaultdict(list)
                for subfield in r.split("$$")[1:]:
                    code, value = subfield.strip().split(" ", 1)
                    sfd_dict[code].append(value)
                # Finally, create a Field962 linked to the BibRecord.
                fld = Field962.objects.create(
                    bib_record=bib,
                    cat_center=sfd_dict.get("a", [""])[0],
                    cataloger=sfd_dict.get("b", [""])[0],
                    yyyymm=sfd_dict.get("c", [""])[0][0:6],
                    difficulty=sfd_dict.get("d", [""])[0],
                    maint_info=sfd_dict.get("g", [""])[0],
                )
                # Repeatable subfields
                for sfd_code in ["h", "i", "j", "k"]:
                    sfd_list = sfd_dict.get(sfd_code, None)
                    if sfd_list:
                        for sfd_value in sfd_list:
                            RepeatableSubfield.objects.create(
                                field_962=fld,
                                subfield_code=sfd_code,
                                subfield_value=sfd_value,
                            )
        except Exception as ex:
            print(ex)
            pp.pprint(row)

    # end for row in report_data
    logger.info(f"{replaced_bibs=}")
    logger.info(f"{BibRecord.objects.count()=}")
    logger.info(f"{Field962.objects.count()=}")
    logger.info(f"{RepeatableSubfield.objects.count()=}")


def list_to_string(list):
    return ", ".join(list)


def refresh_all_data():
    # Start with clean database, removing bibs and related fields
    BibRecord.objects.all().delete()
    # Years from 2007 to current year
    years = [y for y in range(dt.now().year, 2006, -1)]
    for year in years:
        # Analytics API calls can fail for various reasons
        # Try any given year 3 times, then move on.
        for attempt in range(1, 4):
            try:
                report_data = run_report(year)
                add_data_to_db(report_data)
            except Exception as ex:
                logger.error(f"ERROR: Failure {attempt} at {year}: {ex}")
            else:
                break
        else:
            print(f"ERROR: Total failure for {year}")


class Command(BaseCommand):
    help = "Refresh local database with catstats data from Alma Analytics"

    def add_arguments(self, parser):
        parser.add_argument(
            "-m",
            "--yyyymm",
            type=str,
            required=True,
            help="YYYYMM to fetch data for, or ALL",
        )

    def handle(self, *args, **options):
        yyyymm = options["yyyymm"]
        if yyyymm == "ALL":
            refresh_all_data()
        else:
            report_data = run_report(yyyymm)
            add_data_to_db(report_data)
