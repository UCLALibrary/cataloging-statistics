import logging
from copy import deepcopy
from django.db.models import Count, F
from django.shortcuts import render
from .forms import CatStatsForm
from .models import BibRecord, Field962, RepeatableSubfield
from catstats.view_utils import get_crosstab_data, get_difficulties, get_summary_data, get_calendar_year, get_fiscal_year

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
			logger.info(f'{filters = }')

			# Always apply form filters to data.
			# Mandatory filter on year & month, but can be different ranges.
			yyyymm = filters['year'] + filters['month']
			report_period = filters['report_period']
			if report_period == 'cy':
				start_yyyymm, end_yyyymm = get_calendar_year(yyyymm)
			elif report_period == 'fy':
				start_yyyymm, end_yyyymm = get_fiscal_year(yyyymm)
			else:
				# Use the same value for both
				start_yyyymm, end_yyyymm = (yyyymm, yyyymm)
			report_data = Field962.objects.filter(yyyymm__gte=start_yyyymm, yyyymm__lte=end_yyyymm)
			# Mandatory filter, but TODO: Support 'All' as an option
			report_data = report_data.filter(cat_center__exact=filters['cat_center'])
			# Optional filters
			if filters['cataloger'] != '':
				report_data = report_data.filter(cataloger__exact=filters['cataloger'])
			if filters['language_code'] != '':
				report_data = report_data.filter(bib_record__language_code__exact=filters['language_code'])
			if filters['place_code'] != '':
				report_data = report_data.filter(bib_record__place_code__exact=filters['place_code'])
			# Project requires special handling as 962 $k is repeatable
			if filters['f962_k_code'] != '':
				report_data = report_data.filter(
					id__in=RepeatableSubfield.objects.filter(
						subfield_code__exact='k', subfield_value__exact=filters['f962_k_code']
						).values('field_962')
					)

			report_code = filters['report']
			# List of difficulty values, needed for several reports
			difficulties = get_difficulties(report_code)

			# Each report gets different filters and either crosstab or summary layout
			if report_code == '01':
				# New titles by format & difficulty
				# Filter on difficulties
				report_data = report_data.filter(difficulty__in=difficulties)
				# Get just the relevant data: List of dictionaries with difficulty, resource_type, count
				report_data = report_data.values(
					'difficulty',
					format=F('bib_record__resource_type')
					).annotate(count=Count('id'))
				headers, display_data = get_crosstab_data(report_data, 'format', 'difficulty')
			elif report_code == '02':
				# National contributions by format
				# Join subfield records with field-level report data
				recs_h = RepeatableSubfield.objects.filter(
					subfield_code__exact='h',
					field_962__in=report_data
					).select_related('field_962__bib_record')
				# Get just the relevant data: List of dictionaries with national_info, resource_type, count
				recs_h = recs_h.values(
					national_info=F('subfield_value'), 
					format=F('field_962__bib_record__resource_type')
					).annotate(count=Count('id'))
				headers, display_data = get_crosstab_data(recs_h, 'format', 'national_info')
			elif report_code == '03':
				# Authority contributions
				all_vals = RepeatableSubfield.objects.filter(
					subfield_code__in=['i', 'j'], 
					field_962__in=report_data
					).values_list('subfield_value', flat=True)
				# Generic headers
				headers = ['Value', 'Count']
				display_data = get_summary_data(all_vals)
			elif report_code == '04':
				# Maintenance by format & difficulty
				# Filter on difficulties
				report_data = report_data.filter(difficulty__in=difficulties)
				# Get just the relevant data: List of dictionaries with difficulty, resource_type, count
				report_data = report_data.values(
					'difficulty', 
					format=F('bib_record__resource_type')
					).annotate(count=Count('id'))
				headers, display_data = get_crosstab_data(report_data, 'format', 'difficulty')
			elif report_code == '05':
				# Maintenance (broad)
				# Filter on difficulties
				all_vals = report_data.filter(difficulty__in=difficulties).values_list('difficulty', flat=True)
				# Generic headers
				headers = ['Value', 'Count']
				display_data = get_summary_data(all_vals)
			elif report_code == '06':
				# Maintenance (details)
				all_vals = report_data.filter(maint_info__gt='').values_list('maint_info', flat=True)
				# Generic headers
				headers = ['Value', 'Count']
				display_data = get_summary_data(all_vals)

		return render(request, 'catstats/catstats.html', {
			'form': form, 
			'headers': headers,
			'display_data': display_data,
			})
	else:
		form = CatStatsForm()
		report_data = []
		return render(request, 'catstats/catstats.html', {'form': form})
