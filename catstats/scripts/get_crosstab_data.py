# Convert report data to cross-tab compatible
def get_crosstab_data(report_data, difficulties):
	# Get counts by format for each cataloging difficulty in difficulties, including totals.
	# Returns ordered list of lists for easy output in HTML template.

	# List of (resource type, difficulty) for rows having one of the desired difficulties.
	# Still unclear if we need to support multiple $d per 962 field.
	# IF USING DICT OF LISTS......
	#vals = [(r['Resource Type'], r['F962']['d'][0]) for r in report_data if r['F962']['d'][0] in difficulties]
	# IF USING REGULAR DICTIONARY.......
	vals = [(r['Resource Type'], r['F962']['d']) for r in report_data if r['F962']['d'] in difficulties]
	# Dictionary of tuple: count from vals
	counts = {val:vals.count(val) for val in vals}
	# Only values which are used
	formats = sorted(set([val[0] for val in vals]))
	diffs = sorted(set([val[1] for val in vals]))

	data_dict = { format: [counts.get((format, diff), 0) for diff in diffs] for format in formats}
	# Add totals
	for k in data_dict:
		data_dict[k].append(sum(data_dict[k]))

	# Data for template is list of lists
	column_headers = ['Format'] + diffs + ['Total']
	total_row = ['Totals'] + [sum(i) for i in zip(*data_dict.values())]
	# Keep only data rows where the row total (final column) is positive.
	data_rows = [[k] + v for k,v in data_dict.items() if v[-1] > 0]
	data_rows.append(total_row)
	return column_headers, data_rows

