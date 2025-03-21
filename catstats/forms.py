import calendar
from datetime import datetime as dt
from django import forms

REPORTS = [
    ("01", "1: New titles by format & difficulty"),  # was 01
    ("02", "2: National contributions by format"),  # was 11
    ("03", "3: Authority contributions"),  # was 06
    ("04", "4: Maintenance by format & difficulty"),  # was 02
    ("05", "5: Maintenance (broad)"),  # was 09
    ("06", "6: Maintenance (details)"),  # was 10
]
# From https://docs.library.ucla.edu/x/EilACw
CAT_CENTERS = [
    ("ALL", "--- ALL ---"),
    ("clk", "Clark Library"),
    ("eal", "East Asian Library"),
    ("ethno", "Ethnomusicology Archive"),
    ("ftva", "Film and Television Archive"),
    ("iml", "Instructional Media Lab"),
    ("law", "Law Library"),
    ("lsc", "Library Special Collections"),
    ("rams", "RAMS"),
    ("ues", "University Elementary School"),
]

# Number and first 3 letters of months, in list of tuples for HTML form
# Format m 1..12 as strings '01'..'12'
MONTHS = [(str(m).zfill(2), calendar.month_name[m][0:3]) for m in range(1, 13)]

REPORT_PERIODS = [("ym", "Month only"), ("fy", "Fiscal year"), ("cy", "Calendar year")]


def _get_years() -> list[tuple[int, int]]:
    # Years from 2007 to current year, in list of tuples for HTML form
    # Final value of range isn't included
    return [(y, y) for y in range(dt.now().year, 2006, -1)]


class CatStatsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This needs to be set in __init__() so that it is evaluated whenever
        # the form is loaded. Otherwise, these values are calculated and set
        # only at application start, and can be wrong if the application is not
        # restarted when a new year begins.
        self.fields["year"] = forms.ChoiceField(choices=_get_years())

    report = forms.ChoiceField(
        choices=REPORTS,
    )
    # Cataloging center, from bib 962 $a
    cat_center = forms.ChoiceField(
        choices=CAT_CENTERS,
    )
    # Placeholder for year so it's positioned correctly;
    # values are set in __init__().
    year = forms.ChoiceField()
    # year and month are combined for searching the bib 962 $c, selected by yyyymm only
    month = forms.ChoiceField(
        choices=MONTHS,
    )
    # Report period (given year/month, full calendar year, full fiscal year)
    report_period = forms.ChoiceField(choices=REPORT_PERIODS)
    # Cataloger's initials, from bib 962 $b
    cataloger = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "size": 10,
                "placeholder": "Initials",
            }
        ),
        required=False,
    )
    # MARC bib language code
    language_code = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "size": 5,
                "max_length": 3,
                "placeholder": "Code",
            }
        ),
        required=False,
    )
    # MARC bib place code
    place_code = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "size": 5,
                "max_length": 3,
                "placeholder": "Code",
            }
        ),
        required=False,
    )
    # MARC bib 962 $k, used for some projects
    f962_k_code = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "size": 25,
                "placeholder": "962 $k code",
            }
        ),
        label="962 $k code",
        required=False,
    )
