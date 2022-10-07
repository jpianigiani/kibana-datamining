# kibana-datamining

---------------------------------------------------------------------------------
 This tool is supposed to be run on the developer/maintainer local laptop, connected via VPN and using ssh-forwarding to issue API calls to the lab Elasticsearch cluster in NBG99x. Although it is called Kibana Datamining, it actually fetches data from ElasticSearch itself.

The ssh-proxy configuration ,as well the elasticsearch URL, is in configdata.json: the selection of the ENDPOINT name (via the -e parameter) (and the elasticsearch data view e.g fluentd.* = syslogs, alarms= nims-ca-em*) allows to select the ElasticSearch Data view  to visualize alarms, logs , or vendor specific logs.

------------------



{
        
 {
    "common":{                
        "proxies": {
                "https": "socks5h://127.0.0.1:5000",
                "http": "socks5h://127.0.0.1:5000"
                },
        "headers":{
                    "Content-Type": "application/json",
                    "kbn-xsrf": "True"
                }
        },    
     "logs":{
                "url":"http://172.23.95.77:9200/fluentd.*/_search",
                "fields":["@timestamp","_index","host","ident","severity","message"],
                "timestamp_field":"@timestamp",
                "report_type_prefix":"logs"
            },

    "hpe_logs":{
                "url":"http://172.23.95.77:9200/fluentd.nims-ca-logs-hpe*/_search",
                "fields":["@timestamp","_index","host","ident","severity","message"],
                "timestamp_field":"@timestamp",               
                "report_type_prefix":"logs"


            },
    "contrailinsight_logs":{
                "url":"http://172.23.95.77:9200/fluentd.nims-ca-log-contrailinsights*/_search",           
                "fields":["@timestamp","_index","host","ident","severity","message"],
                "timestamp_field":"@timestamp",               
                "report_type_prefix":"logs"

            },
    "alarms":{
                "url":"http://172.23.95.77:9200/nims-ca-em*/_search",
                "fields":["@timestamp","_index","Host","ident","ci-id","severity","data_source","fluentd_tag","summary","additional_text",
                "nims-alarm.alarmrawdata.state","nims-alarm.nimsmetainfo.identifier"],
                "timestamp_field":"@timestamp",               
                "report_type_prefix":"alarms"
            }
}
in the example above, i am using port 5000 forwarding to nbg992 by "ssh -o ServerAliveInterval=59 -ND 5000 DT_Nbg992_Shell"

---------------------------------------------------------------------------------
## Required files
In order for the tool to run on a local laptop to connect to NBG99x Elasticsearch, you need the following files:
- kibanaminer.py
- report_library.py
- query_generic.json
- kibanaminer.json
- kibanaminer-errors.json
- configdata.json

The output files containing elasticsearch complete response and the flattened down version of the response are in the same folder, under kibanaminer.out and kibanaminer.short.out AND kibanaminer.medium.out (containing .short.out plus the data parsing results) respectively)
The human readable formatted report is saved under ./REPORT directory from where the kibanaminer.py runs. This is configurable under the kibanaminer.json file (key: "Files")

Whenever the tool is run using the option -n --NOTES <string>, the CLI command is appended under ELASTICSEARCH.QUERIES.LOG json file.
        Structure is <string>, <FROM-TO of query ><Endpoint being queried><timestamp of query execution > <Command line with params>
        
---------------------------------------------------------------------------------
## Python dependencies
The following libraries are used in **report_library.py:
- import json
- import string
- import sys
- import glob
- import os
- import math
- import re
- from datetime import datetime
- import traceback
- from aop_logger import aop_logger
    
and in **kibanaminer.pt
- import json
- import requests
- import math
- import os, sys
- import argparse
- from datetime import datetime,timedelta
- import time
- import string
- from report_library import dynamic_report, parameters,report,menu
- import re
- import getch


---------------------------------------------------------------------------------
# Using the tool
---------------------------------------------------------------------------------
python3 kibanaminer.py -h
usage: kibanaminer.py [-h] [-f FROM [FROM ...]] [-t TO [TO ...]] [-w WORDS [WORDS ...]] [-x EXCLUDEWORDS [EXCLUDEWORDS ...]] [-i] [-d] [-r RECORDS] [-e ENDPOINT] [-n NOTES]

optional arguments:
  -h, --help            show this help message and exit
  -f FROM [FROM ...], --FROM FROM [FROM ...]
                        Specify from when to start fetching logs (YYYY-MM-DDTHH:MM:SS or MMM-DD HH:MM .. many supported date time formats! e.g. 2022-09-20 15:42, 20-sep 15:42, sep-20 15:42 or ElasticSearch format which is
                        2022-09-20T15:42 (defaults: for year: current year, for time: 00:00 if omitted)). If completely omitted, default is Now-1day
  -t TO [TO ...], --TO TO [TO ...]
                        Specify to when to fetch logs (YYYY-MM-DDTHH:MM:SS or MMM-DD HH:MM .. many supported date time formats!). If omitted=Now
  -w WORDS [WORDS ...], --WORDS WORDS [WORDS ...]
                        List of space-separated words to search for, in the query
  -x EXCLUDEWORDS [EXCLUDEWORDS ...], --EXCLUDEWORDS EXCLUDEWORDS [EXCLUDEWORDS ...]
                        List of space-separated words to EXCLUDE from the query results
  -i, --INTERACTIVE     If specified, interactive menu is presented after each record to navigate through the records, on screen, providing options to search for specific values in resulting records.
  -d, --DEBUG           If specified, DEBUG mode set to true
  -r RECORDS, --RECORDS RECORDS
                        N. of hits returned by query, default=1000
  -e ENDPOINT, --ENDPOINT ENDPOINT
                        ElasticSearch Data view to query: logs (default) for logs, alarms for alarms. See configdata.json keys
  -n NOTES, --NOTES NOTES
                        Description of what you are looking for.. Every time the tool is run with -n option, the CLI command line string is saved with the -n KEY in file ELASTICSEARCH.QUERIES.LOG JSON file
---------------------------------------------------------------------------------
EXAMPLES:
        
python3 kibanaminer.py -i
- fetches all the records and displays in INTERACTIVE MODE, starting with now()-24hours to now(). User can go over each record and browse the results on screen

python3 kibanaminer.py -f 2022-09-16t12:26 
- fetches all the records starting with the specified date:time (please note : small 't' between date and time, in this format
- default value for -f is now()-24 hours
** NOTE: now the date is parsed in different formats: YMD, DMY, MDY, DAY-MON, MONth-DAY, and parsed into datetime. There is no need to add the 'T' between Date and time, as required in Elasticsearch query as from the CLI arguments (date and time can be provided as 2022/09/13,14:52 or 14/12/2021 07:21) the dates are matched agains three regex (YMD, DMY and MDY formats) and then converted to datetime values, before being passed to ElasticSearch into the query as strings

python3 kibanaminer.py -f 2022-09-16t12:26  -t 2022-09-18t18:55
- fetches all records between those dates. Default value for -t is now()

python3 kibanaminer.py -f 2022-09-16t12:26  -t 2022-09-18t18:55 -w s43 hpe error
- fetches all records between those dates which CONTAIN any of the three words ['s43', 'hpe', 'error'] in ANY of the fields

python3 kibanaminer.py -f 2022-09-16t12:26  -t 2022-09-18t18:55 -x info warn
- fetches all records between those dates which DO NOT CONTAIN any of the three words ['info', 'warn'] in ALL of the fields

python3 kibanaminer.py -f 2022-09-16t12:26  -t 2022-09-18t18:55 -w s43 hpe error -x info warn
- fetches all records between those dates which CONTAIN any of the three words ['s43', 'hpe', 'error'] in ANY of the fields and DO NOT CONTAIN any of the three words ['info', 'warn'] in ALL of the fields

python3 kibanaminer.py -f 2022-09-16t12:26  -t 2022-09-18t18:55 -w s43 hpe error -x info warn -d
- same as above, runs in DEBUG mode. 

python3 kibanaminer.py -f 2022-09-16t12:26  -t 2022-09-18t18:55 -w s43 hpe error -x info warn -r 2500
- Same as above, requests elasticsearch to provide 2500 records if available. Default is 1000, i tried up to 10000 and it works
        
python3 kibanaminer.py -f 2022-09-16t12:26  -t 2022-09-18t18:55 -w s43 hpe error -x info warn -r 2500 -n QUERY_FOR_S43_SEP16
- Same as above. The CLI command line with parameters is also saved under key "QUERY_FOR_S43_SEP16" in ELASTICSEARCH.QUERIES.LOG JSON file

---------------------------------------------------------------------------------
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

### kibanaminer.json : configuration data for the report_library.py module
This json files contains all the configuration data for the report_library.py module.
- Syslog configuration data under key "syslog"
- Report Keys, sorting keys and multiline_keys under "Reports_Keys"
- Length of each field is under FieldLenghts. Those fields which contain multiple values are also present under "FieldLists" (length of each entry)
- FieldTransforms contains the customizable function to apply for each reportField before printing
- FieldTransformsAttributes contains two keys (corresponding to two distinct report object methods: split_string and message_parser). These two keys contain the regex expressions to be applied. the split_String call is used to extract information (resulttype) from a string using regex. the message_parser is more specific for kibanaminer.py and it is used to parse all fields via all regexes to extract as much valuable info from a elasticsearch message

### REPORT_LIBRARY.PY : class report
a Report is an object storing structured data. each report has a set of attributes:
- a NAME (set_name), which is used for the filename where the report is saved (every printout on screen of a report corresponds to also saving the report as a file)
- a TYPE (e.g. KIBANA_LOG_REPORT, MESSAGE_PARSE.. VM_REPORT): the type is used as the INITIAL STRING that identifies the different keys of that report e.g. if name=KIBANA_LOG_REPORT, in the kibanaminer.json file, the keys of these reports are under "KIBANAMINER_LOG_KEYS":{"key1":20....}
- different set of keys identifying the fields (columns) of the report: 
- - report_type_KEYS: contains the keys for this report
- - report_type_SORTING_KEYS: contains  the keys by which the report data are sorted by <report object>sort_report()
  - report_type_MULTILINE_KEYS: contains a dict like {"0":[ "key2", "key1"],"1":["key3]} that is used to print a report record over multiple lines (0 is the first line, 1 is the second and so on..)
  
--------------------------------------------
The report object contains 
- Data structure to store (2D array) the data constituting a report
- Methods to manipulate records (add, search), to get keys for that report 
- Methods for records processing e.g. deriving data from record entries via regex. For Kibanaminer.py, the most relevant is "def message_parser()" which does the actual regex parsing of elasticsearch records. In other apps as resource_analysis.py, regex parsing is used e.g. to derive the vnf name or vnfc name or the lineup from the vnf name
- Methods to "transform" the data before visualizing it (def ApplyTransforms), which applies custom functionality on each key (as specified in the kibanaminer.json, under the key "FieldTransforms" . These are custom functions apply to each record entry value via eval() before passing the transformed record to the Linewrapper for printing/visualization
- Methods for printing and saving the reports (def print_report) including indentation and text wrapping (see def LineWrapper_V2)
