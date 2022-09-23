# kibana-datamining

This tool is supposed to be run on the developer/maintainer local laptop, connected via VPN and using ssh-forwarding to issue API calls to the lab Elasticsearch cluster in NBG99x. Although it is called Kibana Datamining, it actually fetches data from ElasticSearch itself.

Tool software structure:
The tool is composed of two modules (kibanaminer.py and report_library.py). 
Kibanaminer.py 
- contains the Elasticsearch/Kibana specific objects that establish the connection to elasticsearch via ssh proxy
- Creates the request toward ElasticSearch in accordance to the parameter passed in the CLI  as arguments typically:
- - FROM=query data from this date:time, 
- - TO= query data until this date:time; 
- - WORDS= words that must be present in the record ; 
- - EXCLUDEWORDS=words that must NOT be present in the record
- - DEBUG : run in debug mode (quite verbose, to be used eventually when adding new regexes to filter data out of the records)
- - INTERACTIVE : once the data are fetched (and parsed), they are shown on screen through an interactive menu
- Receives the response from ElasticSearch, saves it and transforms into a flat JSON data structure {"record progressive number":{ subset of ElasticSearch fields in "key":"value"}
- 
