# -----------------------------------------------------------
# J.Pianigiani, August 17 2022
# -----------------------------------------------------------
import json
import requests
import math
import os, sys
import argparse
from datetime import datetime,timedelta
import time
import string
import dateutil.parser as dparser
from report_library import dynamic_report, parameters,report,menu
import logging
import re
import getch




class kibanaminer():

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    White = '\033[97m'
    Yellow = '\033[93m'
    Magenta = '\033[95m'
    Grey = '\033[90m'
    Black = '\033[90m'
    Backg_Yellow= '\033[1;42m'
    Backg_Default='\033[1;0m'
    Backg_Red_ForeG_White= '\033[40;7m'+White
    Backg_Green='\033[1;42m'
    Default = '\033[99m'

    QueryFilter_IncludeBlock= {
                                "bool": {
                                    "must_not": {
                                        "phrase": 
                                            {
                                            "type": "best_fields",
                                            "query": "TEXTTOEXCLUDE",
                                            "lenient": True
                                        }
                                    }
                                }
                            }
    QueryFilter_ExcludeBlock={
                                "bool": {
                                    "must_not": {
                                        "phrase": 
                                            {
                                            "type": "best_fields",
                                            "query": "TEXTTOEXCLUDE",
                                            "lenient": True
                                        }
                                    }
                                }
                            }
#------------------------------------------------------------------------------------------------------------------------------------

    def __init__(self, args):
        self.screenrows, self.screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh = int(self.screencolumns)
        self.Stringa0="{0: ^"+str(self.ScreenWitdh)+"}"
        self.FOREANDBACKGROUND='\033[38;5;{:d};48;5;{:d}m'
        self.RESETCOLOR='\033[0m'
        self.CONFIGFILENAME="configdata.json"
        self.QUERYFILENAME="query_generic.json"
        with open(self.CONFIGFILENAME,"r") as file2:
            self.configdata=json.load(file2)
        #self.TwoLevelParseFields=configdata["two_level_parse"]
        self.ENDPOINT=args.ENDPOINT
        self.NOTES=args.NOTES

        if self.ENDPOINT in self.configdata.keys():
            self.elastic_url = self.configdata[self.ENDPOINT]["url"]
            self.Endpoint_specific_ReportType=self.configdata[args.ENDPOINT]["report_type_prefix"].upper()

        else:
            print(self.FOREANDBACKGROUND.format(255,9)+self.Stringa0.format( ("Available endpoints in configdata.json: {:}. CLI command requested endpoint is {:}".format(list(self.configdata.keys()),self.ENDPOINT))))
            print(self.RESETCOLOR)
            exit(-1)

        # Each Endpoint in Elasticsearch may (and will ) have distinct fields e.g. alarms from nims-ca-em have different fields than
        # fluentd* for logs. So distinct report keys must exist for eac report type.
        # Upon creating the Kibanaminer object, the report type (part of report_library.py) needs to be set 
        # in report_library, report type is the INITIAL string to match the report keys so it is important to have distinct keys for logs and alarms, since the elasticsearch fields are different for those two cases

        self.FieldsList=self.configdata[self.ENDPOINT]["fields"]
        self.ReportTypePerEndPoint = self.configdata[self.ENDPOINT]["report_type_prefix"].upper()

        self.session = requests.Session()
        self.session.verify = False
        self.session.proxies =self.configdata["common"]["proxies"] 
        print(self.session.proxies)
        self.HEADERS = self.configdata["common"]["headers"]
        self.query={}
        self.DEBUG=args.DEBUG
        if self.DEBUG:
            print("DEBUG Mode")

        self.SearchFilter={}


    def parse_date(self, passed_values_list, returntype="kibana"):
        dateregex=[]
        timeregex=[]
        year_now=datetime.strftime(datetime.now(),"%Y")
        stringa="(?P<YMD>(?P<YEAR>(?P<Y>20[0-9]{2})[-\/\.])(?P<M>[0][1-9]|1[0-2]|[1-9])[-\/\.](?P<D>[0][1-9]|[1-2][0-9]|3[0-1]|[1-9]))"
        dateregex.append(stringa)
        stringa="(?P<DMY>(?P<D>[0][1-9]|[1-2][0-9]|3[0-1]|[1-9])[-\/\.](?P<M>[0][1-9]|1[0-2]|[1-9])(?P<YEAR>[-\/\.](?P<Y>20[0-9]{2})))"
        dateregex.append(stringa)
        stringa="(?P<MDY>(?P<M>[0][1-9]|1[0-2]|[1-9])[-\/\.](?P<D>[0][1-9]|[1-2][0-9]|3[0-1]|[1-9])(?P<YEAR>[-\/\.](?P<Y>20[0-9]{2})))"
        dateregex.append(stringa)
        stringa="(?P<DDMON>(?P<D>[0][1-9]|[1-2][0-9]|3[0-1]|[1-9])[-\/\.](?P<M>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?P<YEAR>[-\/\.](?P<Y>20[0-9]{2}))?)"
        dateregex.append(stringa)
        stringa="(?P<DDMON>(?P<M>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-\/\.](?P<D>[0][1-9]|[1-2][0-9]|3[0-1]|[1-9])(?P<YEAR>[-\/\.](?P<Y>20[0-9]{2}))?)"
        dateregex.append(stringa)
        timeregex.append("(?P<HMS>(?P<HH>[0-1]?[0-9]|2[0-3])[:\.](?P<MM>[0-5][0-9])[:\.]?(?P<SS>[0-5][0-9])?)")
        #timeregex.append("(([0-1]?[0-9]|2[0-3])[:\.]([0-5][0-9]))")

        if type(passed_values_list)==list:
            string_to_parse=" ".join(passed_values_list).lower()
        elif type(passed_values_list)==str:
            string_to_parse=passed_values_list
        else:
            print("wrong type of passed value to parse date: ",passed_values_list)
            print(type(passed_values_list))
            exit(-1)
        datematch=False
        for item in dateregex:
            regex=re.compile(item)
            result_iterator=[OneSearch for OneSearch in regex.finditer(string_to_parse)]
            for SearchResult in result_iterator:
                Result_Dict = SearchResult.groupdict()
                if not Result_Dict['Y']:
                    Result_Dict['Y']=year_now
                normalized_datevalue=Result_Dict["Y"]+'-'+Result_Dict["M"].rjust(2,'0')+'-'+Result_Dict["D"].rjust(2,'0')
                if "DDMON" in Result_Dict.keys():
                    format1="%Y-%b-%d"
                else:
                    format1="%Y-%m-%d"
                datematch=True
                print("\nitem:",item,"\nDATE REGEX: normalized_datevalues:",normalized_datevalue)                    
            if datematch:
                break  
        if not datematch:
                print("ERROR - no valid date provided :", string_to_parse, ": did not find match on ", item)
                exit(-1)

        timematch=False

        for item in timeregex:
            regex=re.compile(item)
            result_iterator=[OneSearch for OneSearch in regex.finditer(string_to_parse)]
            for SearchResult in result_iterator:
                Result_Dict = SearchResult.groupdict()
                if "HMS" in Result_Dict.keys():
                    format1+=" %H:%M:%S"                
                    timematch=True
                    if not Result_Dict['SS']:
                        Result_Dict['SS']="00"
                    normalized_timevalue=Result_Dict["HH"]+':'+Result_Dict["MM"].rjust(2,'0')+':'+Result_Dict["SS"].rjust(2,'0')

                else:
                    print("no valid time provided :", string_to_parse,".. using 00:00:00 as default")
                    normalized_timevalue="00:00:00"
            if timematch:
                break
        if not timematch:
            normalized_timevalue="00:00:00"
            format1+=" %H:%M:%S"                

        actual_datetimevalue_string=normalized_datevalue+' '+normalized_timevalue
        print("FINAL: actual_datetimevalue_string :",actual_datetimevalue_string)
        actual_datetimevalue=datetime.strptime(actual_datetimevalue_string,format1)
        print("FINAL: actual_datetimevalue :",actual_datetimevalue)
                
        if returntype=="kibana":
            return_string=datetime.strftime(actual_datetimevalue,"%Y-%m-%dT%H:%M:%S")
            print(return_string)
            return (return_string,actual_datetimevalue)
        

    def initialize_filter_from_args(self,args):
        self.QueryFrom, self.QueryFromDatetime= self.parse_date(args.FROM)
        self.QueryTo,self.QueryToDatetime= self.parse_date(args.TO)
        self.QueryRunAt =datetime.now()

        self.localRegexDict={}
        if args.WORDS:
            if self.DEBUG:
                print("Words to include:", args.WORDS)
            Regexstring="("+"|".join(args.WORDS)+")"
            self.localRegexDict["WORDSREGEX"]=Regexstring
            self.localRegexDict["WORDSLIST"]=args.WORDS
            self.localRegexDict["WORDS"]=re.compile(Regexstring)
            self.localRegexDict["WORDSFLAG"]=True
            if self.DEBUG: 
                print("Including only records matching the words:", self.FAIL,Regexstring, self.Yellow)
        else:
            self.localRegexDict["WORDSFLAG"]=False
        
        if args.EXCLUDEWORDS:
            print("Words to exclude:", args.EXCLUDEWORDS)
            Regexstring="("+"|".join(args.EXCLUDEWORDS)+")"
            print("EXCLUDE WORDS: RegexString:",Regexstring)
            self.localRegexDict["EXCLUDEWORDSLIST"]=args.EXCLUDEWORDS
            self.localRegexDict["EXCLUDEWORDSREGEX"]=Regexstring

            self.localRegexDict["EXCLUDEWORDS"]=re.compile(Regexstring)
            self.localRegexDict["EXCLUDEWORDSFLAG"]=True
            if self.DEBUG: 
                print("Excluding records matching the words:", self.FAIL,Regexstring, self.Yellow)

        else:
            self.localRegexDict["EXCLUDEWORDSFLAG"]=False
        
        self.RECORDSTOGET=args.RECORDS
        stringa1= self.Stringa0.format( (" Next query filter : from {:} to {:}".format(self.QueryFrom,self.QueryTo)))
        print(self.FOREANDBACKGROUND.format(0,255)+stringa1+self.RESETCOLOR)



    def log_elasticsearch_query(self,args):
        def namespace_to_dict(namespace):
            return {
                    k: namespace_to_dict(v) if isinstance(v, argparse.Namespace) else v
                    for k, v in vars(namespace).items()
                }
        # SAVE QUERY DETAIL IN ELASTICSEARCH.QUERIES.LOG file
        print(args)
        self.UniqueQueryId= {}
        self.ExecutionTime=datetime.strftime(datetime.now(),"%Y%m%d-%H%M%S")
        #print("EXECUTION TIME: ", ExecutionTime)
        try:
            with open("ELASTICSEARCH.QUERIES.LOG","r") as file1:
                TRANSFORMEDDICT= json.load(file1) 
                #print(json.dumps(ExecutionLog,indent=4))
        except:
            TRANSFORMEDDICT={}

        TempDictWithArgs=namespace_to_dict(args)
        self.Notes=TempDictWithArgs["NOTES"].upper()
        self.CombinedFromToString=self.QueryFrom+self.QueryTo
        self.Endpoint=TempDictWithArgs["ENDPOINT"]
        TempDictWithArgs["FROM"]=self.QueryFrom
        TempDictWithArgs["TO"]=self.QueryTo

        #self.UniqueQueryId[self.ExecutionTime]["CMDLINE"]=" ".join(sys.argv)
        #ExecutionLog[self.ExecutionTime]=self.UniqueQueryId[self.ExecutionTime]


        if self.Notes not in TRANSFORMEDDICT.keys():
            TRANSFORMEDDICT[self.Notes]={}
        if self.CombinedFromToString not in TRANSFORMEDDICT[self.Notes].keys():
            TRANSFORMEDDICT[self.Notes][self.CombinedFromToString]={}
        if self.Endpoint not in TRANSFORMEDDICT[self.Notes][self.CombinedFromToString].keys():
            TRANSFORMEDDICT[self.Notes][self.CombinedFromToString][self.Endpoint]={}
        TRANSFORMEDDICT[self.Notes][self.CombinedFromToString][self.Endpoint][self.ExecutionTime]={}
        CMDLINE="python3 kibanaminer.py "
        for Item in TempDictWithArgs.keys():
            if isinstance(TempDictWithArgs[Item],str):
                CMDLINE+='--'+Item+' '+TempDictWithArgs[Item]+' '
            elif  isinstance(TempDictWithArgs[Item],list):
                CMDLINE+='--'+Item+' '+" ".join(TempDictWithArgs[Item])+' '
            elif  isinstance(TempDictWithArgs[Item],bool):
                if TempDictWithArgs[Item]:
                    CMDLINE+='--'+Item+' '
        TRANSFORMEDDICT[self.Notes][self.CombinedFromToString][self.Endpoint][self.ExecutionTime]["CommandLine"]=CMDLINE
        #TRANSFORMEDDICT[self.Notes][self.CombinedFromToString][self.Endpoint][self.ExecutionTime]["Record"]=TempDictWithArgs

        #print(json.dumps(TRANSFORMEDDICT,indent=4))
        print(self.FOREANDBACKGROUND.format(255,9)+self.Stringa0.format("TIMESTAMP FOR THIS QUERY :"+self.ExecutionTime)+self.RESETCOLOR)

        if self.Notes!="DEFAULT":
            with open("ELASTICSEARCH.QUERIES.LOG","w") as file1:
                file1.write(json.dumps(TRANSFORMEDDICT,indent=4))
            Stringa="QUERY SAVED IN ELASTICSEARCH.QUERIES.LOG, under keys: {:}, {:}, {:}".format(self.Notes,self.CombinedFromToString, self.Endpoint)
            print(self.FOREANDBACKGROUND.format(255,9)+self.Stringa0.format(Stringa)+self.RESETCOLOR)
        else:
            Stringa="This query and its CLI parameters will not be saved in file ELASTICSEARCH.QUERIES.LOG"
            print(self.FOREANDBACKGROUND.format(255,9)+self.Stringa0.format(Stringa)+self.RESETCOLOR)



 

#------------------------------------------------------------------------------------------------------------------------------------
    def set_filter(self):

        with open(self.QUERYFILENAME, "r") as file1:
                self.query = json.load(file1)
        self.query["size"]= self.RECORDSTOGET
        filterlist= self.query["query"]["bool"]["filter"]
        AddTimeFilter=True
        AddWordFilter=True
        for QueryItem in filterlist:
            #print(QueryItem)
            if "range" in QueryItem.keys():
                AddTimeFilter=False
                break

        if AddTimeFilter==False:
                #print("range key present")
                QueryItem["range"]["@timestamp"]["gte"]=self.QueryFrom
                QueryItem["range"]["@timestamp"]["lte"]=self.QueryTo
        else :
                QueryFilterRoot={
                    "range": 
                        {
                            "@timestamp": 
                                {
                                "format": "strict_date_optional_time",
                                "gte": "",
                                "lte": ""
                                }
                        }
                    }
                QueryFilterRoot["range"]["@timestamp"]["gte"]=self.QueryFrom
                QueryFilterRoot["range"]["@timestamp"]["lte"]=self.QueryTo      
                filterlist.append(QueryFilterRoot)

        for QueryItem in filterlist:
            #print(QueryItem)
            if "bool" in QueryItem.keys():
                AddWordFilter=False
        if AddWordFilter==False:
            print("UNHANDLED!")
            exit(-1)
        else :
                QueryFilterRoot=        {
                            "bool": {
                                        "filter": [
     
                                        ]
                                    }
                            }

                #print("args.WORDS:",args.WORDS)
                count=0
                QueryFilterItem=[]
                if self.localRegexDict["WORDSFLAG"]:
                    for WordToAdd in self.localRegexDict["WORDSLIST"]:
                        #QueryFilterItem.append({
                        #    "multi_match": {
                        #        "type": "best_fields",
                        #        "query": "FREE TEXT SEARCH",
                        #        "lenient": True
                        #        }
                        #    })
                        #QueryFilterItem[count]["multi_match"]["query"]=WordToAdd                     
                        QueryFilterItem.append({
                            "multi_match": {
                                #"type": "phrase",
                                "type": "phrase",
                                "query": "wordtomatchhere",
                                "lenient": True
                                }
                            })
                        QueryFilterItem[count]["multi_match"]["query"]=WordToAdd
                        QueryFilterRoot["bool"]["filter"].append(QueryFilterItem[count])
                        #print("Adding word : ",WordToAdd)
                        #print(QueryFilterItem)
                        #print(QueryFilterRoot)
                        count+=1



                if self.localRegexDict["EXCLUDEWORDSFLAG"]:
                    for WordToAdd in self.localRegexDict["EXCLUDEWORDSLIST"]:
                        QueryFilterItem.append({
                                "bool": {
                                "must_not": {
                                    "multi_match": {
                                    "type": "phrase",
                                    "query": "WORDTOEXCLUDEGOESHERE",
                                    "lenient": True
                                    }
                                }
                                }
                            } )
                        QueryFilterItem[count]["bool"]["must_not"]["multi_match"]["query"]=WordToAdd
                        QueryFilterRoot["bool"]["filter"].append(QueryFilterItem[count])
                        #print("Adding excludeword : ",WordToAdd)
                        #print(QueryFilterItem)
                        #print(QueryFilterRoot)
                        count+=1
                filterlist.append(QueryFilterRoot)
        print(json.dumps(self.query, indent=5))


#------------------------------------------------------------------------------------------------------------------------------------

    def get_data_from_kibana(self):
        Timeout=22
        try:
            self.request = self.session.get(self.elastic_url, headers=self.HEADERS, json=self.query,timeout=Timeout)
        except requests.exceptions.Timeout as e:
            print("-"*100)
            print("Connection to Elasticsearchcluster timed out after {:} seconds".format(Timeout))
            print("Please check connectivity to ssh proxy , in case used, in file configdata.json, reported below:")
            print(json.dumps(self.configdata[self.ENDPOINT],indent=4))
            print("-"*100)
            exit(-1)
        print("response code {}".format(self.request.status_code))
        self.queryresult=self.request.json()
        with open("kibanaminer.rawdata."+self.NOTES+"-"+self.ENDPOINT+"-"+self.ExecutionTime+".out","w") as file1:
            file1.write(json.dumps(self.queryresult,indent=10))
#------------------------------------------------------------------------------------------------------------------------------------
    def transform_data3(self ):

        def get_recursively(search_dict, field):
            if isinstance(search_dict, dict):
                if field in search_dict:
                    return search_dict[field]
                for key in search_dict:
                    item = get_recursively(search_dict[key], field)
                    if item is not None:
                        return item
            elif isinstance(search_dict, list):
                for element in search_dict:
                    item = get_recursively(element, field)
                    if item is not None:
                        return item
            return None

        self.ExcludedCounter=0
        self.transformed_data={}
        self.count=0
        if self.queryresult["hits"]["total"]["value"]==0:
            print(self.FOREANDBACKGROUND.format(255,9))
            print("--------------------------------------------")
            print("transform_data3: NO DATA RETURNED FROM QUERY")
            print("--------------------------------------------"+self.RESETCOLOR)            
            exit(-1)
        else:
            self.RECCOUNT=self.queryresult["hits"]["total"]["value"]
            print("--------------------------------------------")            
            print("TOTAL RECORDS FROM KIBANA: ", self.RECCOUNT)
            print("--------------------------------------------")            
        
        if self.DEBUG:
            print("self.localRegexDict['WORDSFLAG']:",self.localRegexDict["WORDSFLAG"]," self.localRegexDict['EXCLUDEWORDSFLAG']:",self.localRegexDict["EXCLUDEWORDSFLAG"])
            
        for record in self.queryresult["hits"]["hits"]:
            if self.DEBUG:
                print(self.OKGREEN+"--------------------------------------------")            
                print("Record # {:} of {:}".format( self.count,self.RECCOUNT))
                print("--------------------------------------------"+self.Yellow)            
            #self.transformed_data[self.count]={}
            # if no "include word" is present, then all records are considered to be included. 
            #Otherwise all record are not included and they are included only if regex matches
            if self.localRegexDict["WORDSFLAG"]:
                IncludeRecord=False
            else:
                IncludeRecord=True
            ExcludeRecord=False

            temp_results=[]
            temp_result_keys=[]
            temp_result_dict={}

            for mykey in self.FieldsList:
                temp_results=get_recursively(record,mykey)
                #print("DEBUG transform_Data_3")
                if self.DEBUG:
                    print("key:",mykey, "   Temp_result:",temp_results)
                try:
                    value=temp_results.lower()
                except:
                    if self.DEBUG:
                        print("DEBUG: Get recursively did not find result for key:",mykey)
                        print("temp_Results=",temp_results)
                        print(json.dumps(record,indent=5))
                        exit(-1)
                    value=""
                if True:
                    if self.localRegexDict["WORDSFLAG"]:
                        WordsMatchResult=self.localRegexDict["WORDS"].findall(value)
                        if WordsMatchResult:
                            IncludeRecord=True
                            if self.DEBUG:
                                print(self.Yellow+"value:",value, 
                                    self.Grey+" Regex:", self.localRegexDict["WORDSREGEX"],
                                    self.OKBLUE+" WordsMAtchResult=",WordsMatchResult,self.Yellow)
                        else:
                            pass
        

                    if self.localRegexDict["EXCLUDEWORDSFLAG"]:
                        ExcludeWordsMatchResult=self.localRegexDict["EXCLUDEWORDS"].findall(value)
                        if ExcludeWordsMatchResult:
                            ExcludeRecord=True
                            IncludeRecord=False
                            if self.DEBUG:
                                print(self.Yellow+"value:",value, 
                                    self.Grey+" Regex:", self.localRegexDict["EXCLUDEWORDSREGEX"],
                                    self.FAIL+" ExcludeWordsMatchResult=",ExcludeWordsMatchResult,self.Yellow)
                    else:
                        pass

                    temp_result_dict[mykey]=value
                if self.DEBUG:
                    print("DEBUG : temp_result:",temp_result_dict)

            if (IncludeRecord and ExcludeRecord==False) :
                self.transformed_data[self.count]=temp_result_dict
                if self.DEBUG:
                    print("Count:",self.count,"  added:")
                if self.count==0:
                    stringa=self.transformed_data[self.count]["@timestamp"][:-16]
                    self.Tstart=datetime.strptime(stringa,"%Y-%m-%dT%H:%M:%S")
                self.count+=1
            else:
                self.ExcludedCounter+=1
                if self.DEBUG:
                    print("\tExcluded records due to Preliminary Regex: {:}".format(self.ExcludedCounter))
        if self.count==0:
            print("----------------------------------------------------------------------------")
            print("transform_data3: returned 0 records post additional filtering on query data")
            print("----------------------------------------------------------------------------")
            exit(-1)
        self.Tend=datetime.strptime(self.transformed_data[self.count-1]["@timestamp"][:-16],"%Y-%m-%dT%H:%M:%S")
        with open("kibanaminer.short."+self.NOTES+"-"+self.ENDPOINT+"-"+self.ExecutionTime+".out","w") as file1:
            file1.write(json.dumps(self.transformed_data,indent=10))

#------------------------------------------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------------------------------------------

    def message_classifier(self, messagedict):
        pass
#------------------------------------------------------------------------------------------------------------------------------------

    def add_to_report(self, reportobject):
        for item in self.transformed_data.keys():
            if self.DEBUG:
                print("Item:", item,"\n",json.dumps(self.transformed_data[item],indent=5))

            reportobject.addemptyrecord()
            for field in self.FieldsList:
            #["time","timestamp","_index","host","ident","severity","message"]
                reportobject.UpdateLastRecordValueByKey(field,self.transformed_data[item][field])



    def interactive(self, args, DirectionValue):
        if DirectionValue==1:
            DirectionChar='+'
        else:
            DirectionChar='-' 
        TextToDisplay=""
        for k ,v in self.SearchFilter.items():
            TextToDisplay+=k+'='+v
        InputCharacterMap={
            chr(27):{"name":"ESC","title":"Exit","value":0,"action":"exit"},
            "-":{"name":"-","title":"-1 rec","value":-1,"action":"delta"},
            '\n':{"name":"CR","title":DirectionChar+"1 rec","value":1,"action":"delta"},
            "1":{"name":"1","title":DirectionChar+"10 rec","value":10,"action":"delta"},
            "2":{"name":"2","title":DirectionChar+"30 rec","value":30,"action":"delta"},
            "3":{"name":"3","title":DirectionChar+"100 rec","value":100,"action":"delta"},
            "/":{"name":"/","title":"search","value":0,"action":"search", "exit":['\n','/','x1b']},
            "r":{"name":"r","title":"search'"+TextToDisplay+"'","value":0,"action":"repeatsearch", "exit":['\n','/','x1b']},
            "n":{"name":"n","title":"Fetch next recs","value":0,"action":"next"},

            " ":{"name":"<Space>","title":"Direction"+DirectionChar,"value":0,"action":"change"}
        }
        returnFilter=None

        ExitActions=["delta","exit", "change","next"]
        OneChar=''
        var_Continue=True
        ListOfAllowedKeys=list(InputCharacterMap.keys())
        MenuString=''
        for Item in InputCharacterMap.keys():
            MyDict=InputCharacterMap[Item]
            MenuItem=" [{:1s}] {:}   ".format(InputCharacterMap[Item]["name"],InputCharacterMap[Item]["title"])
            MenuString+=MenuItem        
        Stringa=self.FOREANDBACKGROUND.format(255,4)+self.Stringa0.format(MenuString)+self.Backg_Default
        print(Stringa)
        while var_Continue:
            CharSequence=''
            while OneChar not in ListOfAllowedKeys:
                OneChar=getch.getch().lower()
                #print(ascii(ch))
                CharSequence+=OneChar.lower()
            returnAction= InputCharacterMap[OneChar]["action"]
            returnValue=InputCharacterMap[OneChar]["value"]
            if returnAction in ExitActions:
                if returnAction=="change":
                    DirectionValue=-1*DirectionValue
                var_Continue=False
                returnFilter=None
                returnValue*=DirectionValue

            elif returnAction == "repeatsearch":
                returnFilter={}
                if len(self.SearchFilter.keys())>0:
                    for k in self.SearchFilter.keys():
                        returnFilter[k]=self.SearchFilter[k]
                        var_Continue=False
                else:
                    print(self.FOREANDBACKGROUND.format(255,9)+"\tNo previous search string specified. First perform a search with /\t"+self.RESETCOLOR)
                    var_Continue=False
                    returnFilter=None
                    returnAction="delta"
                    returnValue=0

            elif returnAction =="search":
                self.SearchString={}
                MyDict=InputCharacterMap[OneChar]
                CharSequence=''
                OneChar=''
                ExitSearch=False
                MenuItem=self.Backg_Red_ForeG_White+"\tSEARCH : ESC or CR to exit\t"
                count=0
                AllowedInputs=['\n','\x1b']
                for Item in self.FieldsList:
                    MenuItem+="{:1d} {:10s}\t".format(count,Item)
                    AllowedInputs.append(str(count))
                    count+=1
                print(MenuItem)
                OneChar=''
                CharSequence=''
                while OneChar not  in AllowedInputs:
                    OneChar=getch.getche()
                if OneChar not in ['\n','\x1b']:
                    value=int(OneChar)
                    stringa=self.Backg_Red_ForeG_White+"\tsearch field {:} for the following value: "
                    FieldName=self.FieldsList[value]
                    print(stringa.format(FieldName.upper()))
                    returnFilter={FieldName:""}
                    CharSequence=''
                    OneChar=''
                    while OneChar not in MyDict["exit"]:
                        OneChar=getch.getche()
                        if OneChar not in MyDict["exit"]:
                            CharSequence+=OneChar.lower()
                    var_Continue=False
                    returnFilter[FieldName]=CharSequence
                    self.SearchFilter[FieldName]=CharSequence
                    #print("Return Filter:",returnFilter, self.Backg_Default)
                else:
                    var_Continue=True
                    returnFilter=None

        #print("Retvalue:",returnValue," filter:", returnFilter, " action:",returnAction, self.Backg_Default)
        
        return returnValue, returnFilter, returnAction, DirectionValue
            
    def indent(self,text, amount, ch=' '):
        length=len(text)
        width=self.ScreenWitdh
        writablespace=width-amount-1
        lines=math.ceil(length/writablespace)
        retval=""
        for count in range(lines):
            retval+=amount*ch+ text[count*writablespace: min((count+1)*writablespace,length-count*writablespace)]
        #print("Text:",text)
        #print("lines:",lines," length:",length," writable space:",writablespace)
        #print("retval:",retval)
        return retval


#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------
    def scan_and_parse_messages(self, args,reportobject, pars):


        def datetransform(v):
            stringa=v[0:18]+v[28:35]
            timestampvalue=datetime.strptime(stringa.lower(),"%Y-%m-%dt%H:%M:%S%z")
            retval= "\t\t\t\t\t\t\t\t\t\t\t\t\t  ("+datetime.strftime(timestampvalue,"%d-%B %H:%M:%S %p")+" )"
            return retval

        mylist= list(self.transformed_data.keys())
        mylistlen=len(mylist)
        self.enriched_data={}
        #print(mylist)
        key=0
        #for key in self.transformed_data.keys():
        GoOn=True

        Direction=1
        while GoOn:
            os.system('clear')

            if args.WORDS:
                StringaWords=",".join(args.WORDS)
            else:
                StringaWords=""
            if args.EXCLUDEWORDS:
                StringaExclWords=",".join(args.EXCLUDEWORDS)
            else:
                StringaExclWords=""                
            print(self.FOREANDBACKGROUND.format(255,4))
            Stringa1="{:} query from {:15s} to {:15s} : Words included:[{:s}] - Words excluded: [{:s}])".format(self.ENDPOINT,datetime.strftime(self.QueryFromDatetime,"%b %d, %H:%M:%S"),datetime.strftime(self.QueryToDatetime,"%b %d, %H:%M:%S"),StringaWords,StringaExclWords)
            Stringa=self.Stringa0.format(Stringa1)
            print(Stringa)

            Stringa0="{0:_^"+str(pars.ScreenWitdh)+"}"
            Stringa1=" RECORD: {:3d} OF {:3d}  (from {:15s} to {:15s})".format(key,mylistlen-1, datetime.strftime(self.Tstart,"%b %d, %H:%M:%S"),datetime.strftime(self.Tend,"%b %d, %H:%M:%S"))
            Stringa=Stringa0.format(Stringa1)
            Stringa+=self.Backg_Default
            print(Stringa)
            #print(Stringa.format(key,mylistlen))

            #print("Message:\n",message)
            #try:
            #returndictionary = reportobject.message_parser(message)
            returndictionary, modifiedrecord, JSONParsedrecord ,color_legend= reportobject.message_parser(self.transformed_data[key])
            self.enriched_data[key]=self.transformed_data[key]
            if "returndictionary" not in self.enriched_data[key]:
                self.enriched_data[key]["parsed_values"]=returndictionary
                self.enriched_data[key]["data_with_highlights"]=modifiedrecord
                self.enriched_data[key]["json_parsed_values"]=JSONParsedrecord
                #print(json.dumps(self.enriched_data[key]))

            Stringa="{:}"         
            #print(Stringa.format(json.dumps(self.transformed_data[key],indent=5)))
            print(datetransform(self.transformed_data[key]["@timestamp"]))
            for k,v in modifiedrecord.items(): #self.transformed_data[key].items():  
                #print("----------ORIGINAL VALUE ---------------")
                Stringa=self.Default+"{:20s}".format(k)
                Stringa1=Stringa+" : "+"{:}".format(v)
                print(Stringa1)
                if k in JSONParsedrecord:
                    print(self.Backg_Default+self.Default+"--------------JSON PARSED VALUE -----------")
                    JSON_Parsed_Value=json.dumps(JSONParsedrecord[k],indent=3)
                    IndentedJSON=re.sub('\n','\n'+26*' ',JSON_Parsed_Value)
                    Stringa1=Stringa+" : "+"{:}".format(IndentedJSON)
                    print(Stringa1)
            print(self.Backg_Default)
            temp_report = dynamic_report("MESSAGE_PARSE",returndictionary,pars)
            temp_report.print_report(pars)
            temp_report.restore_configdata()
            del temp_report
            

            if args.INTERACTIVE:
                Delta, Filter, action,DirectionRetval=self.interactive(args, Direction)
                Direction=DirectionRetval
                if action=="delta":
                    key+=Delta
                    key%= mylistlen
                    GoOn=True
                    retval=False
                elif action=="exit":
                    retval = False
                    GoOn=False
                elif action=="search" or action=="repeatsearch":
                    matchfound=False
                    fieldname=list(Filter.keys())[0]
                    MatchValue=Filter[fieldname]
                    for counter in range(mylistlen):
                        searchindex=(counter+key) % mylistlen
                        FieldValue=self.transformed_data[searchindex][fieldname]
                        if FieldValue.find(MatchValue)>-1:
                            key=searchindex
                            matchfound=True
                            break
                    if matchfound==False:
                        print(self.FAIL," Did not find any match for {:} in field {:}".format(fieldname,MatchValue),self.Default)
                    GoOn=True
                    Retval=False
                    
                elif action=="next":
                    retval= True
                    GoOn=False
            else:
                key+=1
                if key>=mylistlen:
                    retval= False
                    action=""
                    GoOn=False
        return retval,action,Direction


    def adjust_filter(self, Direction):
        
        TimeCoveredbyPreviousQuery=self.Tend - self.Tstart
        NumberOfRecords = self.RECCOUNT
        print("TimeCoveredbyPreviousQuery = ",TimeCoveredbyPreviousQuery)
        print("Tstart:", self.Tstart)
        print("Tend  :",self.Tend)
        if Direction ==1:
            print("adjust_filter: going forward for next query")
            self.QueryFromDatetime = self.Tend
            PreviousTimeTo =self.QueryToDatetime 
            self.QueryToDatetime=PreviousTimeTo+TimeCoveredbyPreviousQuery
        else:
            print("adjust_filter: going BACKWARD for next query")
            self.QueryToDatetime=self.Tstart
            PreviousTimeFrom =self.QueryFromDatetime
            self.QueryFromDatetime = PreviousTimeFrom-TimeCoveredbyPreviousQuery
            print("previousTime=Tend= ",PreviousTimeFrom)
            print("setting FROM=",self.QueryFromDatetime )
            print("setting TO  =",self.QueryToDatetime )

        self.QueryFrom=datetime.strftime(self.QueryFromDatetime,"%Y-%m-%dT%H:%M:%S")
        self.QueryTo=datetime.strftime(self.QueryToDatetime,"%Y-%m-%dT%H:%M:%S")

        stringa1= self.Stringa0.format( (" Next query filter : from {:} to {:}".format(self.QueryFrom,self.QueryTo)))
        print(self.FOREANDBACKGROUND.format(0,255)+stringa1+self.RESETCOLOR)
#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------
def main(arguments):
    os.system('clear')
    programname= arguments[0].split(".")[0]
    MyPars=parameters(programname)
    MyReport=report(MyPars)
    parser = argparse.ArgumentParser(description="PLEASE REFER TO : https://github.com/jpianigiani/kibana-datamining/blob/main/README.md", 
                                    epilog="------------- developed by J.Pianigiani, 2022 --------------")
    CurrentTime = datetime.now()
    DefaultFromTime=CurrentTime-timedelta(hours=24)
    DefaultTo= CurrentTime.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    DefaultFrom= DefaultFromTime.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    parser.add_argument("-f","--FROM",nargs='+',help="Specify from when to start fetching logs (YYYY-MM-DDTHH:MM:SS or MMM-DD HH:MM .. many supported date time formats! e.g. 2022-09-20 15:42, 20-sep 15:42, sep-20 15:42 or ElasticSearch format which is 2022-09-20T15:42 (defaults: for year: current year, for time: 00:00 if omitted)). If completely omitted, default is Now-1day", default=DefaultFrom, required=False)
    parser.add_argument("-t","--TO",nargs='+',help="Specify to when to fetch logs (YYYY-MM-DDTHH:MM:SS or MMM-DD HH:MM .. many supported date time formats!). If omitted=Now", default=DefaultTo, required=False)
    parser.add_argument("-w","--WORDS", nargs='+', help="List of space-separated words to search for, in the query ", required=False, type=str)
    parser.add_argument("-x","--EXCLUDEWORDS", nargs='+', help="List of space-separated words to EXCLUDE from the query results", required=False, default=[], type=str)
    parser.add_argument("-i","--INTERACTIVE", help="If specified, interactive menu is presented after each record to navigate through the records, on screen, providing options to search for specific values in resulting records.", action='store_true')
    #type=bool, default=False, required=False)
    parser.add_argument("-d","--DEBUG", help="If specified, DEBUG mode set to true", action='store_true')
    parser.add_argument("-r","--RECORDS", help="N. of hits returned by query, default=1000", type=int, default=1000, required=False)
    parser.add_argument("-e","--ENDPOINT", help="ElasticSearch Data view to query: logs (default) for logs, alarms for alarms. See configdata.json keys",  default="logs", required=False)
    parser.add_argument("-n","--NOTES", help="Description of what you are looking for.. Every time the tool is run with -n option, the CLI command line string is saved with the -n KEY in file ELASTICSEARCH.QUERIES.LOG JSON file ",  
            default="DEFAULT", required=False)
    args=parser.parse_args()

    MyElasticSearch=kibanaminer(args)
    MyReport=report(MyPars,MyElasticSearch.Endpoint_specific_ReportType)
    # Initial setting of query parameters
    MyElasticSearch.initialize_filter_from_args(args)
    MyElasticSearch.log_elasticsearch_query(args)

    ContinueHere=True
    while ContinueHere:
        MyElasticSearch.set_filter()
        MyElasticSearch.get_data_from_kibana()
        MyElasticSearch.transform_data3()
        ContinueHere, action , Direction= MyElasticSearch.scan_and_parse_messages(args,MyReport, MyPars)
        if action=="next":
            MyElasticSearch.adjust_filter(Direction)
    enriched_file= open("kibanaminer.medium."+MyElasticSearch.NOTES+"-"+MyElasticSearch.ENDPOINT+"-"+"-"+MyElasticSearch.ExecutionTime+".out","w")
    enriched_file.write(json.dumps(MyElasticSearch.enriched_data,indent=4))
    #MyElasticSearch.add_to_report(MyReport)
    #MyReport.set_name("ELASTICSEARCH"+MyElasticSearch.Endpoint_specific_ReportType+"_REPORT")
    #MyReport.print_report(MyPars)

if __name__ == '__main__':
    main(sys.argv)

