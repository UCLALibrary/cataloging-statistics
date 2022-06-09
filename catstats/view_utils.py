# Supporting functions for view(s)

# Convert report data to cross-tab compatible
def get_crosstab_data(report_data):
	# Only values which are used
	# Data rows for crosstab
	formats = sorted(set([row['resource_type'] for row in report_data]))
	# Data columns for crosstab
	diffs = sorted(set([row['difficulty'] for row in report_data]))

	data_rows = []
	for format in formats:
		data_row = [format]
		row_total = 0
		for diff in diffs:
			count = report_data.filter(resource_type__exact=format, difficulty__exact=diff).values_list('count', flat=True)
			if len(count) == 0:
				val = 0
			else:
				val = count[0]
			data_row.append(val)
			row_total += val
		data_row.append(row_total)
		data_rows.append(data_row)

	# Data for template is list of lists
	column_headers = ['Format'] + diffs + ['Total']
	# Data rows include format as 1st element, so skip that when summing columns.
	if data_rows != []:
		# Didn't find a way to exclude column with zip().
		total_row = ['Totals'] + [ sum(row[i] for row in data_rows) for i in range(1, len(data_rows[0]))]
	else:
		total_row = []
	data_rows.append(total_row)
	# Return column_headers separately to make formatting easier in template.
	return column_headers, data_rows

