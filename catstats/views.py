import logging
from copy import deepcopy
from django.shortcuts import render
from .forms import CatStatsForm
from catstats.scripts import get_catstats_data

logger = logging.getLogger(__name__)

# Placeholder for form in SYS-826; will be fleshed out via SYS-827
def run_report(request):
	if request.method == 'POST':
		form = CatStatsForm(request.POST)
		if form.is_valid():
			# For convenience
			filters = deepcopy(form.cleaned_data)
			logger.info(f'{filters = }')
			report_data = get_catstats_data.main(filters)
	else:
		form = CatStatsForm()
		report_data = {}
	return render(request, 'catstats/catstats.html', {'form': form, 'report_data': report_data})
