import json
import logging
import os
import pprint as pp
import urllib.parse
import xmltodict
from collections import defaultdict
from copy import deepcopy
from catstats.scripts.alma_api_client import Alma_Api_Client

logger = logging.getLogger(__name__)

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
	# By cat center: too slow for RAMS (17+ minutes, 300+ MB data)
# 	filter_xml = f'''
# <sawx:expr xsi:type="sawx:list" op="containsAll" 
# 	xmlns:saw="com.siebel.analytics.web/report/v1.1" 
# 	xmlns:sawx="com.siebel.analytics.web/expression/v1.1" 
# 	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
# 	xmlns:xsd="http://www.w3.org/2001/XMLSchema"
# >
# 	<sawx:expr xsi:type="sawx:sqlExpression">LOWER("Bibliographic Details"."Local Param 02")</sawx:expr>
# 	<sawx:expr xsi:type="xsd:string">$$a {cat_center}</sawx:expr>
# </sawx:expr>
# '''

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

	# Boolean OR not working?
# 	filter_xml = f'''
# <sawx:expr xsi:type="sawx:logical" op="or" 
# 	xmlns:saw="com.siebel.analytics.web/report/v1.1" 
# 	xmlns:sawx="com.siebel.analytics.web/expression/v1.1" 
# 	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
# 	xmlns:xsd="http://www.w3.org/2001/XMLSchema"
# >
# 	<sawx:expr xsi:type="sawx:list" op="like">
# 	<sawx:expr xsi:type="sawx:sqlExpression">"Bibliographic Details"."Local Param 02"</sawx:expr>
# 	<sawx:expr xsi:type="xsd:string">%$$c 202001%</sawx:expr></sawx:expr>
# 	<sawx:expr xsi:type="sawx:list" op="like">
# 	<sawx:expr xsi:type="sawx:sqlExpression">"Bibliographic Details"."Local Param 02"</sawx:expr>
# 	<sawx:expr xsi:type="xsd:string">%$$c 202002%</sawx:expr></sawx:expr>
# </sawx:expr>
# '''
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

def run_report(api_key, yyyymm):
	alma = Alma_Api_Client(api_key)
	report_path = '/shared/University of California Los Angeles (UCLA) 01UCS_LAL/Cataloging/Reports/API/Cataloging Statistics (API)'
	# From form
	#yyyymm = '202101'
	filter_xml = get_filter(yyyymm)

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
		# After first run: use constant = subsequent parameters merged
		report = alma.get_analytics_report(constant_params | subsequent_params)
		report_data = get_report_data(report)
		all_rows.extend(report_data['rows'])

	return {'column_names': column_names, 'rows': all_rows}

def row_is_wanted(row, filters):
	# Compare row values to filters.  If any filter fails, row is not wanted.
	# Filter values all exist, and strings will be '' if filter is not set.
	is_wanted = True
	# Dictionary of lists: code: [val1,...]
	f962 = row['F962']
	# Cataloging center in $a: Filter is always a non-empty string
	if filters['cat_center'] not in f962.get('a', ''):
		is_wanted = False
	# Cataloger initials in $b: Filter may be an empty string
	elif filters['cataloger'] != '' and filters['cataloger'] not in f962.get('b', '').lower():
		is_wanted = False
	# Date in $c is yyyymmdd: Filter is always a non-empty string, yyyymm
	# Still unclear if we need to support multiple $d per 962 field.
	# elif filters['year'] + filters['month'] != f962.get('c', '')[0][0:6]:  # IF USING DICT OF LISTS
	elif filters['year'] + filters['month'] != f962.get('c', '')[0:6]:
		is_wanted = False
	# Difficulty in $d is required: Do not approve rows missing it
	elif f962.get('d') is None:
		is_wanted = False
	# Local value in $k: $k may not exist, and filter may be an empty string
	elif filters['f962_k_code'] != '' and filters['f962_k_code'] not in f962.get('k', ''):
		is_wanted = False
	# Non-962 filters
	elif filters['language_code'] != '' and filters['language_code'] != row['Language Code']:
		is_wanted = False

	return is_wanted

def expand_and_filter_data(report_data, filters=None):
	# Analytics data has 1 row per bib record;
	# multiple 962 fields are combined in ...
	data = []
	column_names = report_data['column_names']
	rows = report_data['rows']
	for row in rows:
		# Update keys to use real column names, removing meaningless Column0
		row = dict([(column_names.get(k), v) for k, v in row.items() if k != 'Column0'])
		# Split rows where Local Param 02 contains multiple 962 fields, delimited by ';'
		fld_962s = row['Local Param 02'].split(';')
		for fld_962 in fld_962s:
			new_row = deepcopy(row)
			r = fld_962.strip()

			# Creates dict of lists, which is a pain
			# sfd_dict = defaultdict(list)
			# for subfield in r.split('$$')[1:]:
			# 	code, value = subfield.strip().split(' ', 1)
			# 	sfd_dict[code].append(value)

			# Creates dictionary: OK except when subfields are repeated, only last value is kept.
			sfd_dict = {code: value for sfd in fld_962.split('$$')[1:] for code, value in [sfd.strip().split(' ', 1)]}
			new_row['F962'] = sfd_dict

			if row_is_wanted(new_row, filters):
				data.append(new_row)

	return data

def main(filters):
	api_key = os.getenv('ALMA_API_KEY')
	logger.info(f'{filters = }')
	yyyymm = filters['year'] + filters['month']
	report_data = run_report(api_key, yyyymm)
	logger.info(f'Data rows retrieved: {len(report_data["rows"]) = }')
	data = expand_and_filter_data(report_data, filters)
	logger.info(f'Data rows after expand/filter: {len(data) = }')
	return data

if __name__ == '__main__':
	main()
