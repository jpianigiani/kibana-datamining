# kibana-datamining

This tool is supposed to be run on the developer/maintainer local laptop, connected via VPN and using ssh-forwarding to issue API calls to the lab Elasticsearch cluster in NBG99x. Although it is called Kibana Datamining, it actually fetches data from ElasticSearch itself.

Tool software structure:
The tool is composed of two modules (kibanaminer.py and report_library.py). 
---- KIBANAMINER.PY ----
Kibanaminer.py which uses TWO input files:
- its configuration data, in file configdata.json, containing ssh proxy parameters, list of fields to extract from elasticsearch
- a json file (query_generic.json) that contains the json structure of a generic elasticsearch query
- contains the Elasticsearch/Kibana specific objects that establish the connection to elasticsearch via ssh proxy
--- KIBANAMINER.PY : main() ---
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
- - 
- Parses each field using REGEX to extract 


