import logging
from copy import deepcopy
from django.db.models import Count, F
from django.shortcuts import render
from .forms import CatStatsForm
from .models import BibRecord, Field962
from catstats.view_utils import get_crosstab_data

logger = logging.getLogger(__name__)

def run_report(request):
	if request.method == 'POST':
		form = CatStatsForm(request.POST)
		if form.is_valid():
			# For brevity and convenience.
			filters = deepcopy(form.cleaned_data)
			# Lower-case specific user-entered filters for later comparison; 
			# no non-ASCII support required.
			lcase_required = ['cataloger', 'f962_k_code', 'language_code', 'place_code']
			for filter in lcase_required:
				filters[filter] = filters[filter].lower()

			report_code = filters['report']
			if report_code == '01':
				# 'New' difficulty codes
				difficulties = ['1', '1+', '2', '2+', '3', '3+', '4', '4+']
			elif report_code == '04':
				# 'Maintenance' difficulty codes
				difficulties = [
					'1+loc', '1+rec', '1+rev', '1loc', '1rec', '1rev', 
					'2+loc', '2+rec', '2+rev', '2loc', '2rec', '2rev', 
					'3+loc', '3+rec', '3+rev', '3loc', '3rec', '3rev', 
					'4+loc', '4+rec', '4+rev', '4loc', '4rec', '4rev']
			else:
				difficulties = None
				raise Exception(f'Report {report_code} not yet implemented')

			# Mandatory filter
			yyyymm = filters['year'] + filters['month']
			report_data = Field962.objects.filter(yyyymm__exact=yyyymm)
			# Mandatory filter, but TODO: Support 'All' as an option
			report_data = report_data.filter(cat_center__exact=filters['cat_center'])
			# Optional filters
			if filters['language_code'] != '':
				report_data = report_data.filter(bib_record__language_code__exact=filters['language_code'])
			if filters['place_code'] != '':
				report_data = report_data.filter(bib_record__place_code__exact=filters['place_code'])
			# TODO: Improve this, since the project field can contain multiple projects, like 'mel, HAYNES'
			if filters['f962_k_code'] != '':
				report_data = report_data.filter(project__iexact=filters['f962_k_code'])


			# Difficulties applies to reports 01 and 04 only
			# Apply relevant difficulties, if any
			if difficulties is not None:
				report_data = report_data.filter(difficulty__in=difficulties)
			# Get just the relevant data: List of dictionaries with difficulty, resource_type, count
			report_data = report_data.values('difficulty', resource_type=F('bib_record__resource_type')).annotate(count=Count('id'))

			# TODO: Handle other, simpler reports.
			headers, crosstab_data = get_crosstab_data(report_data)
		return render(request, 'catstats/catstats.html', {
			'form': form, 
			'headers': headers,
			'crosstab_data': crosstab_data,
			'report_data': report_data,
			})
	else:
		form = CatStatsForm()
		report_data = []
		return render(request, 'catstats/catstats.html', {'form': form})
