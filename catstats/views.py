from django.shortcuts import render
from .forms import CatStatsForm

# Placeholderf for form in SYS-826; will be fleshed out via SYS-827
def run_report(request):
	if request.method == 'POST':
		pass
	else:
		form = CatStatsForm()
	return render(request, 'catstats/catstats.html', {'form': form})
