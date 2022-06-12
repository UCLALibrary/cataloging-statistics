# Supporting functions for view(s)
from collections import Counter

def get_difficulties(report_code):
	if report_code == '01':
		# 'New' difficulty codes
		difficulties = ['1', '1+', '2', '2+', '3', '3+', '4', '4+']
	elif report_code in ['04', '05']:
		# 'Maintenance' difficulty codes
		difficulties = [
			'1+loc', '1+rec', '1+rev', '1loc', '1rec', '1rev',
			'2+loc', '2+rec', '2+rev', '2loc', '2rec', '2rev',
			'3+loc', '3+rec', '3+rev', '3loc', '3rec', '3rev',
			'4+loc', '4+rec', '4+rev', '4loc', '4rec', '4rev']
	else:
		difficulties = None
	return difficulties


def get_summary_data(list_of_data):
	# Transform a list of scalar values into a list of lists,
	# with each being [value, count].
	# E.g., ['a', 'b', 'a'] becomes [['a', 2], ['b', 1]]
	counts = Counter(list_of_data)
	data_rows = sorted([[k,v] for k,v in counts.items()])
	data_rows.append(get_total_row(data_rows))
	return data_rows

def get_total_row(data_rows):
	# Data rows include string as 1st element, so skip that when summing columns.
	if data_rows != []:
		# Didn't find a way to exclude column with zip().
		total_row = ['Totals'] + [ sum(row[i] for row in data_rows) for i in range(1, len(data_rows[0]))]
	else:
		total_row = []
	return total_row


def get_crosstab_data(report_data, row_name, col_name):
	# Generic function returning crosstab (list of lists)
	# on row_name and col_name, with counts and totals.
	# Data rows for crosstab
	rows = sorted(set([row[row_name] for row in report_data]))
	# Data columns for crosstab
	cols = sorted(set([row[col_name] for row in report_data]))

	# For passing variable field names into filter below.
	row_name__exact = row_name + '__exact'
	col_name__exact = col_name + '__exact'

	data_rows = []
	for row in rows:
		data_row = [row]
		row_total = 0
		for col in cols:
			count = report_data.filter(
				**{row_name__exact:row, col_name__exact:col}
				).values_list('count', flat=True)
			if len(count) == 0:
				val = 0
			else:
				val = count[0]
			data_row.append(val)
			row_total += val
		data_row.append(row_total)
		data_rows.append(data_row)

	# Data for template is list of lists
	column_headers = [row_name.title()] + cols + ['Total']
	data_rows.append(get_total_row(data_rows))
	# Return column_headers separately to make formatting easier in template.
	return column_headers, data_rows
