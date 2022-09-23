# kibana-datamining

This tool is supposed to be run on the developer/maintainer local laptop, connected via VPN and using ssh-forwarding to issue API calls to the lab Elasticsearch cluster in NBG99x. Although it is called Kibana Datamining, it actually fetches data from ElasticSearch itself.

# Tool software structure:
The tool is composed of two modules (kibanaminer.py and report_library.py).

## KIBANAMINER.PY 
Kibanaminer.py which uses TWO input files:
- its configuration data, in file configdata.json, containing ssh proxy parameters, list of fields to extract from elasticsearch
- a json file (query_generic.json) that contains the json structure of a generic elasticsearch query
- contains the Elasticsearch/Kibana specific objects that establish the connection to elasticsearch via ssh proxy

### KIBANAMINER.PY : main() 
main(), in Kibanaminer.py performs the following tasks:
- Creates the request toward ElasticSearch in accordance to the parameter passed in the CLI  as arguments typically:
- --------------------------- CLI PARAMETERS ------------------------------
- - FROM (-f) : query data from this date:time, 
- - TO (-t) query data until this date:time; 
- - WORDS (-w) words that must be present in the record ; 
- - EXCLUDEWORDS (-x) : words that must NOT be present in the record
- - DEBUG (-d) : run in debug mode (quite verbose, to be used eventually when adding new regexes to filter data out of the records)
- - INTERACTIVE (-i) : once the data are fetched (and parsed), they are shown on screen through an interactive menu to go through the record, perform searches of strings
- - RECORDS (-r) : number of records to receive from ELasticSearch.Default is 1000, but consider that Fluentd produces something like 200K records per hour...
- --------------------------------------------------------------------------
- Receives the response from ElasticSearch, saves it and transforms into a flat JSON data structure {"record progressive number":{ subset of ElasticSearch fields in "key":"value"}
- Parses each field using REGEX and string extraction tecniques to extract relevant information, that is then visualized on the screen and stored to produce a file (for this , kibanaminer.py uses the report_library.py module)
- Produces a human readable report (and saves it to disk, as well saves the elasticsearch data in a json file)

## REPORT_LIBRARY.PY ----
This module is the improved version of mycapacitymodule.py (used in aop_tools/resource_analysis pipelines to produce VM report, NUMA report etc..). 
This module contains the objects :
- parameters: read the module specific json files (name of the application running main(), so in this case it is kibanaminer.json and kibanaminer-errors.json, which contains the Error codes the application casts) that contains the field keys, lengths, used to produce, visualize and print the reports as well the regexes to be used for message parsing. This object also contains the error handling functions (that are integrated with aop_logger)
- report : parent report object containing all methods to manipulate records in a report, print reports and save them to disk
- dynamic report: a child object of report that creates a report object by input of a JSON flat dictionary 
- menu: contains only RGB color codes and escape sequences to change visualization of data/reports

### REPORT_LIBRARY.PY : class report
a Report is an object storing structured data. each report has a set of attributes:
- a NAME (set_name), which is used for the filename where the report is saved (every printout on screen of a report corresponds to also saving the report as a file)
- a TYPE (e.g. KIBANA_LOG_REPORT, MESSAGE_PARSE.. VM_REPORT): the type is used as the INITIAL STRING that identifies the different keys of that report e.g. if name=KIBANA_LOG_REPORT, in the kibanaminer.json file, the keys of these reports are under "KIBANAMINER_LOG_KEYS":{"key1":20....}
- different set of keys identifying the fields (columns) of the report: 
- - report_type_KEYS: contains the keys for this report
- - report_type_SORTING_KEYS: contains  the keys by which the report data are sorted by <report object>sort_report()
  - report_type_MULTILINE_KEYS: contains a dict like {"0":[ "key2", "key1"],"1":["key3]} that is used to print a report record over multiple lines (0 is the first line, 1 is the second and so on..)
  
- - 
The report object contains 
- Data structure to store (2D array) the data constituting a report
