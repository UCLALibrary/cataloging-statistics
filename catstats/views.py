import logging
from copy import deepcopy
from django.shortcuts import render
from .forms import CatStatsForm
from catstats.scripts import get_catstats_data, get_crosstab_data

logger = logging.getLogger(__name__)

def run_report(request):
	if request.method == 'POST':
		form = CatStatsForm(request.POST)
		if form.is_valid():
			# For convenience
			filters = deepcopy(form.cleaned_data)
			# Lower-case specific user-entered filters for later comparison; 
			# no non-ASCII support required.
			lcase_required = ['cataloger', 'f962_k_code', 'language_code', 'place_code']
			for filter in lcase_required:
				filters[filter] = filters[filter].lower()
			logger.info(f'{filters = }')

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
				raise Exception(f'Report {report_code} not yet implemented')

			# Get data from Alma Analytics, filtered as needed
			report_data = get_catstats_data.main(filters)
			# Applies to reports 01/04 only
			headers, crosstab_data = get_crosstab_data.get_crosstab_data(report_data, difficulties)
		return render(request, 'catstats/catstats.html', {
			'form': form, 
			'headers': headers,
			'crosstab_data': crosstab_data,
			})
	else:
		form = CatStatsForm()
		report_data = []
		return render(request, 'catstats/catstats.html', {'form': form})
