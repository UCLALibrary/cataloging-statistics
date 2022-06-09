import json
import logging
import os
import pprint as pp
import urllib.parse
import xmltodict
from collections import defaultdict
from datetime import datetime as dt
from django.core.management.base import BaseCommand
from catstats.models import BibRecord, Field962
from catstats.scripts.alma_api_client import Alma_Api_Client

def get_real_column_names(report_json):
    # Column names are buried in metadata
    # Get dictionary of column info
    # This seems to be available only on initial run (first set of data, not subsequent ones),
    # even if col_names = true parameter is always passed to API.
    column_names = {}
    try:
        column_info = report_json['ResultXml']['rowset']['xsd:schema']['xsd:complexType']['xsd:sequence']['xsd:element']
        # Create mapping of generic column names (Column0 etc.) to real column names
        for row in column_info:
            generic_name = row['@name']
            real_name = row['@saw-sql:columnHeading']
            column_names[generic_name] = real_name
    except KeyError:
        # OK to swallow this error
        pass
    return column_names

def get_filter(yyyymm):
    # By year/month: quick enough, usually 5000-10000 rows
    # No need for LOWER with just digits
    filter_xml = f'''
<sawx:expr xsi:type="sawx:list" op="like" 
    xmlns:saw="com.siebel.analytics.web/report/v1.1" 
    xmlns:sawx="com.siebel.analytics.web/expression/v1.1" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
>
    <sawx:expr xsi:type="sawx:sqlExpression">"Bibliographic Details"."Local Param 02"</sawx:expr>
    <sawx:expr xsi:type="xsd:string">%$$c {yyyymm}%</sawx:expr>
</sawx:expr>
'''
    # Strip out formatting characters which make API unhappy
    return filter_xml.replace('\n', '').replace('\t', '')

def get_report_data(report):
    # Report available only in XML
    # Entire XML report is a "list" with one value, in 'anies' element of json response
    xml = report['anies'][0]
    # Convert xml to python dict intermediate format
    xml_dict = xmltodict.parse(xml)
    # Convert this to real json
    report_json = json.loads(json.dumps(xml_dict))
    # Everything is in QueryResult dict
    report_json = report_json['QueryResult']
    
    # Actual rows of data are a list of dictionaries, in this dictionary
    rows = report_json['ResultXml']['rowset']['Row']

    # Clean up
    report_data = {
        'rows': rows,
        'column_names': get_real_column_names(report_json),
        'is_finished': report_json['IsFinished'], # should always exist
        'resumption_token': report_json.get('ResumptionToken'), # may not exist
    }

    return report_data


def run_report(filter):
    print(f'Running with {filter = }....')
    api_key = os.getenv('ALMA_API_KEY')
    alma = Alma_Api_Client(api_key)
    report_path = '/shared/University of California Los Angeles (UCLA) 01UCS_LAL/Cataloging/Reports/API/Cataloging Statistics (API)'

    filter_xml = get_filter(filter)

    # No need to URL-encode anything, since requests library does that automatically
    constant_params = {
        'col_names': 'true',
        'limit': 1000 # valid values: 25 to 1000, best as multiple of 25
    }
    initial_params = {
        'path': report_path,
        'filter': filter_xml,
    }
    # First run: use constant + initial parameters merged
    batch_number = 1
    print(f'Fetching batch #{batch_number}')
    report = alma.get_analytics_report(constant_params | initial_params)
    report_data = get_report_data(report)
    all_rows = report_data['rows']
    # Preserve column_names as they don't seem to be set on subsequent runs
    column_names = report_data['column_names']

    # Use the token from first run in all subsequent ones
    subsequent_params = {
        'token': report_data['resumption_token'],
    }

    while report_data['is_finished'] == 'false':
        batch_number += 1
        print(f'Fetching batch #{batch_number}')
        # After first run: use constant = subsequent parameters merged
        try:
            report = alma.get_analytics_report(constant_params | subsequent_params)
            report_data = get_report_data(report)
            all_rows.extend(report_data['rows'])
        except Exception as ex:
            pp.pprint(ex)
            pp.pprint(report['api_response'])
            raise

    # Replace 'Column0' etc. names with real names, discarding unwanted Column0
    data = []
    for row in all_rows:
        # Update keys to use real column names, removing meaningless Column0
        row = dict([(column_names.get(k), v) for k, v in row.items() if k != 'Column0'])
        data.append(row)

    return data

def add_data_to_db(report_data):
    print(f'{len(report_data) = }')
    skipped_bibs = 0
    for row in report_data:
        # Each row is one bib, with 1+ 962 fields embeded in 'Local Param 02'.
        mmsid = row['MMS Id']
        if BibRecord.objects.filter(mmsid=mmsid).exists():
            skipped_bibs += 1
        else:
            # First save the bib-level data
            bib = BibRecord.objects.create(
                mmsid=mmsid,
                language_code=row.get('Language Code', ''),
                place_code=row.get('Place Code', ''),
                material_type=row.get('Material Type', ''),
                resource_type=row.get('Resource Type', '')
                )
            # Split rows where Local Param 02 contains multiple 962 fields, delimited by ';'
            for fld_962 in row['Local Param 02'].split(';'):
                r = fld_962.strip()
                # Creates dict of lists, which is a pain
                sfd_dict = defaultdict(list)
                for subfield in r.split('$$')[1:]:
                  code, value = subfield.strip().split(' ', 1)
                  sfd_dict[code].append(value)
                  #pp.pprint(sfd_dict)
                # Finally, create a Field962 linked to the BibRecord.
                # Some repeatable subfields need to be collapsed into one delimited string for storage.
                fld = Field962.objects.create(
                    bib_record=bib,
                    cat_center=sfd_dict.get('a', [''])[0],
                    cataloger=sfd_dict.get('b', [''])[0],
                    yyyymm=sfd_dict.get('c', [''])[0][0:6],
                    difficulty=sfd_dict.get('d', [''])[0],
                    maint_info=sfd_dict.get('g', [''])[0],
                    national_info=list_to_string(sfd_dict.get('h', [''])),
                    naco_info=list_to_string(sfd_dict.get('i', [''])),
                    saco_info=list_to_string(sfd_dict.get('j', [''])),
                    project=list_to_string(sfd_dict.get('k', [''])),
                    )
    # end for row in report_data
    print(f'{skipped_bibs = }')
    print(f'{BibRecord.objects.count() = }')
    print(f'{Field962.objects.count() = }')

def list_to_string(list):
    return ', '.join(list)

def refresh_all_data():
    # Start with clean database, removing bibs and related fields
    BibRecord.objects.all().delete()
    # Years from 2007 to current year
    years = [y for y in range(dt.now().year, 2006, -1)]
    for year in years:
        # Analytics API calls can fail for various reasons
        # Try any given year 3 times, then move on.
        for attempt in range(1,4):
            try:
                report_data = run_report(year)
                add_data_to_db(report_data)
            except Exception as ex:
                print(f'ERROR: Failure {attempt} at {year}: {ex}')
            else:
                break
        else:
            print(f'ERROR: Total failure for {year}')


class Command(BaseCommand):
    help = 'Refresh local database with catstats data from Alma Analytics'

    def add_arguments(self, parser):
        parser.add_argument('-m', '--yyyymm', type=str, required=True,
                            help='YYYYMM to fetch data for, or ALL')

    def handle(self, *args, **options):
        yyyymm = options['yyyymm']
        if yyyymm == 'ALL':
            refresh_all_data()
        else:
            print('TODO: Incremental db update, replacing existing data instead of skipping it')

