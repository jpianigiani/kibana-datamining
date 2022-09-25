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
        self.CONFIGFILENAME="configdata.json"
        self.QUERYFILENAME="query_generic.json"
        with open(self.CONFIGFILENAME,"r") as file2:
            configdata=json.load(file2)
        #self.TwoLevelParseFields=configdata["two_level_parse"]
        self.FieldsList=configdata[args.ENDPOINT]["fields"]

        self.elastic_url = configdata[args.ENDPOINT]["url"]
        self.session = requests.Session()
        self.session.verify = False
        self.session.proxies =configdata[args.ENDPOINT]["proxies"] 
        print(self.session.proxies)
        self.HEADERS = configdata[args.ENDPOINT]["headers"]
        self.query={}
        self.DEBUG=args.DEBUG
        if self.DEBUG:
            print("DEBUG Mode")
        self.screenrows, self.screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh = int(self.screencolumns)

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

        string_to_parse=" ".join(passed_values_list).lower()

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
                    datematch=True
                    if not Result_Dict['SS']:
                        Result_Dict['SS']="00"
                    normalized_timevalue=Result_Dict["HH"]+':'+Result_Dict["MM"].rjust(2,'0')+':'+Result_Dict["SS"].rjust(2,'0')
                else:
                    print("no valid time provided :", string_to_parse,".. using 00:00:00 as default")
                    normalized_timevalue="00:00:00"

        
        actual_datetimevalue_string=normalized_datevalue+' '+normalized_timevalue
        actual_datetimevalue=datetime.strptime(actual_datetimevalue_string,format1)
        print("FINAL: actual_datetimevalue :",actual_datetimevalue)
                
        if returntype=="kibana":
            return_string=datetime.strftime(actual_datetimevalue,"%Y-%m-%dT%H:%M:%S")
            print(return_string)
            return (return_string,actual_datetimevalue)
        

#------------------------------------------------------------------------------------------------------------------------------------
    def set_filter(self, args):
       
        self.QueryFrom, self.QueryFromDatetime= self.parse_date(args.FROM)
        #self.QueryFrom_DateTime=datetime.strptime(self.QueryFrom,"%Y-%m-%d %H:%M:%S")
        self.QueryTo,self.QueryToDatetime= self.parse_date(args.TO)
        #self.QueryTo_DateTime=datetime.strptime(self.QueryTo,"%Y-%m-%d %H:%M:%S")

        self.localRegexDict={}
        if args.WORDS:
            print("Words to include:", args.WORDS)
            Regexstring="("+"|".join(args.WORDS)+")"
            print("WORDS: RegexString:",Regexstring)

            self.localRegexDict["WORDSREGEX"]=Regexstring

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

            self.localRegexDict["EXCLUDEWORDSREGEX"]=Regexstring

            self.localRegexDict["EXCLUDEWORDS"]=re.compile(Regexstring)
            self.localRegexDict["EXCLUDEWORDSFLAG"]=True
            if self.DEBUG: 
                print("Excluding records matching the words:", self.FAIL,Regexstring, self.Yellow)

        else:
            self.localRegexDict["EXCLUDEWORDSFLAG"]=False
        #print("DEBUG: WORDSFLAG=",self.localRegexDict["WORDSFLAG"])
        #print("DEBUG: EXCLUDEWORDSFLAG=",self.localRegexDict["EXCLUDEWORDSFLAG"])

        with open(self.QUERYFILENAME, "r") as file1:
                self.query = json.load(file1)
        self.query["size"]= args.RECORDS
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
                QueryFilterRoot["range"]["@timestamp"]["gte"]=args.FROM
                QueryFilterRoot["range"]["@timestamp"]["lte"]=args.TO       
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
                    for WordToAdd in args.WORDS:
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
                    for WordToAdd in args.EXCLUDEWORDS:
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
        self.request = self.session.get(self.elastic_url, headers=self.HEADERS, json=self.query)
        print("response code {}".format(self.request.status_code))
        self.queryresult=self.request.json()
        with open("kibanaminer.out","w") as file1:
            file1.write(json.dumps(self.queryresult,indent=10))
#------------------------------------------------------------------------------------------------------------------------------------
    def transform_data3(self,arguments ):

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
            print("--------------------------------------------")
            print("transform_data3: NO DATA RETURNED FROM QUERY")
            print("--------------------------------------------")            
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
                            #print(self.Yellow+"value:",value, 
                            #    self.Grey+" Regex:", 
                            #    self.localRegexDict["WORDSREGEX"],
                            #    self.Yellow+" no match")                        

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
                        #print(self.Yellow+"value:",value, 
                        #self.Grey+" Regex:", 
                        #self.localRegexDict["EXCLUDEWORDSREGEX"],
                        #self.Yellow+" no match")         
                    temp_result_dict[mykey]=value
                if self.DEBUG:
                    print("DEBUG : temp_result:",temp_result_dict)

            if (IncludeRecord and ExcludeRecord==False) :
                self.transformed_data[self.count]=temp_result_dict
                if self.DEBUG:
                    print("Count:",self.count,"  added:")
                if self.count==0:
                    self.Tstart=self.transformed_data[self.count]["@timestamp"]
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
        self.Tend=self.transformed_data[self.count-1]["@timestamp"]
        with open("kibanaminer.short.out","w") as file1:
            file1.write(json.dumps(self.transformed_data,indent=10))

#------------------------------------------------------------------------------------------------------------------------------------

    def transform_data2(self, arguments):
        self.ExcludedCounter=0
        self.transformed_data={}
        self.count=0
        if self.queryresult["hits"]["total"]["value"]==0:
            print("--------------------------------------------")
            print("transform_data2: NO DATA RETURNED FROM QUERY")
            print("--------------------------------------------")            
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

            temp_result={}
            for mykey in self.FieldsList:
                if mykey in record.keys():
                    root=record
                else:
                    root= record["_source"]
                try:
                    stringvalue = root[mykey]
                except:
                    print("transform_data2: error fetching key={:} from Elastic records".format(mykey))
                    print("JSON Dumps of record from Elastic is the following:")
                    print(json.dumps(record,indent=10))
                    exit(-1)
                #print("----------------------------")
                #print("stringvalue:")
                #print(stringvalue)
                #print("of type: ", type(stringvalue))
                try:
                    value=json.load (stringvalue.lower())
                    #print("DICT!:", value)
                except:
                    value=stringvalue.lower()

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
                            #print(self.Yellow+"value:",value, 
                            #    self.Grey+" Regex:", 
                            #    self.localRegexDict["WORDSREGEX"],
                            #    self.Yellow+" no match")                        

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
                        #print(self.Yellow+"value:",value, 
                        #self.Grey+" Regex:", 
                        #self.localRegexDict["EXCLUDEWORDSREGEX"],
                        #self.Yellow+" no match")         
                temp_result[mykey]=value
                #print("temp_result:",temp_result)

            if (IncludeRecord and ExcludeRecord==False) :
                self.transformed_data[self.count]=temp_result
                if self.DEBUG:
                    print("Count:",self.count,"  added:")
                if self.count==0:
                    self.Tstart=self.transformed_data[self.count]["@timestamp"]
                self.count+=1
            else:
                self.ExcludedCounter+=1
                if self.DEBUG:
                    print("\tExcluded records due to Preliminary Regex: {:}".format(self.ExcludedCounter))
        if self.count==0:
            print("----------------------------------------------------------------------------")
            print("transform_data2: returned 0 records post additional filtering on query data")
            print("----------------------------------------------------------------------------")
            exit(-1)
        self.Tend=self.transformed_data[self.count-1]["@timestamp"]
        with open("kibanaminer.short.out","w") as file1:
            file1.write(json.dumps(self.transformed_data,indent=10))

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

        InputCharacterMap={
            "q":{"name":"Q","title":"Exit","value":0,"action":"exit"},
            chr(27):{"name":"ESC","title":"Exit","value":0,"action":"exit"},
            "-":{"name":"-","title":"Previous","value":-1,"action":"delta"},
            '\n':{"name":"CR","title":DirectionChar+"1 record","value":1,"action":"delta"},
            "1":{"name":"1","title":DirectionChar+"10 record","value":10,"action":"delta"},
            "2":{"name":"2","title":DirectionChar+"30 record","value":30,"action":"delta"},
            "3":{"name":"3","title":DirectionChar+"100 record","value":100,"action":"delta"},
            "/":{"name":"/","title":"search","value":0,"action":"search", "exit":['\n','/','x1b']},
            " ":{"name":"<Space>","title":"Direction"+DirectionChar,"value":0,"action":"change"}
        }

        ExitActions=["delta","exit", "change"]
        OneChar=''
        var_Continue=True
        ListOfAllowedKeys=list(InputCharacterMap.keys())
        MenuString=self.Backg_Red_ForeG_White
        for Item in InputCharacterMap.keys():
            MyDict=InputCharacterMap[Item]
            MenuItem=" [{:1s}] {:12s}   ".format(InputCharacterMap[Item]["name"],InputCharacterMap[Item]["title"])
            MenuString+=MenuItem
        MenuString+=self.Backg_Default
        print(MenuString)
        while var_Continue:
            CharSequence=''
            while OneChar not in ListOfAllowedKeys:
                OneChar=getch.getch()
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

            if returnAction =="search":
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

    def new_query_timewindow(self, args):
        pass


#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------
    def scan_and_parse_messages(self, args,reportobject, pars):
        mylist= list(self.transformed_data.keys())
        mylistlen=len(mylist)
        self.enriched_data={}
        #print(mylist)
        key=0
        #for key in self.transformed_data.keys():
        GoOn=True

        Direction=1
        while GoOn:
            #print("key:",key, " len of keys:",mylistlen)
            #message=[ self.transformed_data[key]["_index"], self.transformed_data[key]["message"]]
            #try:
            #    message=[]
            #    messagekeys=[]
            #    for field in self.TwoLevelParseFields :
            #        #print("DEBUG: Adding ", field, " to message ",message, " from ",self.transformed_data[key] )
            #        if field in self.transformed_data[key].keys():
            #            message.append (self.transformed_data[key][field])
            #            messagekeys.append(field)
            #except:
            #    print("scan_and_parse_messages: message:",message)
            #    print("scan_and_parse_messages: Field:",field)
            #    exit(-1)
            #print("MESSAGE:", message)
            print(self.Backg_Yellow)
            Stringa0="{0:_^"+str(pars.ScreenWitdh)+"}"
            Stringa1=" RECORD: {:3d} OF {:3d}  (from {:s} to {:s})".format(key,mylistlen,self.Tstart,self.Tend)
            Stringa=Stringa0.format(Stringa1)
            Stringa+=self.Backg_Default
            print(Stringa)
            #print(Stringa.format(key,mylistlen))

            #print("Message:\n",message)
            #try:
            #returndictionary = reportobject.message_parser(message)
            returndictionary, modifiedrecord, JSONParsedrecord = reportobject.message_parser(self.transformed_data[key])
            self.enriched_data[key]=self.transformed_data[key]
            if "returndictionary" not in self.enriched_data[key]:
                self.enriched_data[key]["parsed_values"]=returndictionary
                self.enriched_data[key]["data_with_highlights"]=modifiedrecord
                self.enriched_data[key]["json_parsed_values"]=JSONParsedrecord
                #print(json.dumps(self.enriched_data[key]))


            Stringa="{:}"         
            #print(Stringa.format(json.dumps(self.transformed_data[key],indent=5)))
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
            
            #except:
            #    print("kibanaminer.py:scan_and_parse_messages - error searching {:} in {:}".format(key,message))
            if args.INTERACTIVE:

                Delta, Filter, action,DirectionRetval=self.interactive(args, Direction)
                Direction=DirectionRetval
                if action=="delta":
                    key+=Delta
                    key%= mylistlen
                elif action=="exit":
                    
                    return False
                elif action=="search":
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
                elif action=="next":
                    return True
            else:
                key+=1
                if key>=mylistlen:
                    return False



#------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------
def main(arguments):
    os.system('cls')
    programname= arguments[0].split(".")[0]
    MyPars=parameters(programname)
    MyReport=report(MyPars)
    parser = argparse.ArgumentParser()
    CurrentTime = datetime.now()
    DefaultFromTime=CurrentTime-timedelta(hours=24)
    DefaultTo= CurrentTime.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    DefaultFrom= DefaultFromTime.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    parser.add_argument("-f","--FROM",nargs='+',help="Specify from when to start fetching logs (%Y-%m-%dT%H:%M:%S). If omitted=Now-1day", default=DefaultFrom, required=False)
    parser.add_argument("-t","--TO",nargs='+',help="Specify to when to fetch logs( %Y-%m-%dT%H:%M:%S.000Z). If omitted=Now", default=DefaultTo, required=False)
    parser.add_argument("-w","--WORDS", nargs='+', help="List of space-separated words to search in logs", required=False, type=str)
    parser.add_argument("-x","--EXCLUDEWORDS", nargs='+', help="List of space-separated words to EXCLUDE in logs", required=False, default=[], type=str)
    parser.add_argument("-i","--INTERACTIVE", help="If specified, interactive menu is presented after each record to navigate", action='store_true')
    #type=bool, default=False, required=False)
    parser.add_argument("-d","--DEBUG", help="If specified, DEBUG mode set to true", action='store_true')
    parser.add_argument("-r","--RECORDS", help="N. of hits returned by query, default=1000", type=int, default=1000, required=False)
    parser.add_argument("-e","--ENDPOINT", help="ElasticSearch Data view to query: logs (default) for logs, alarms for alarms. See configdata.json",  default="logs", required=False)

    args=parser.parse_args()
    MyKibana=kibanaminer(args)
    ContinueHere=True
    while ContinueHere:
        MyKibana.set_filter(args)
        MyKibana.get_data_from_kibana()
        MyKibana.transform_data3(args)
        ContinueHere = MyKibana.scan_and_parse_messages(args,MyReport, MyPars)
    enriched_file= open("kibanaminer.medium.out","w")
    enriched_file.write(json.dumps(MyKibana.enriched_data,indent=4))
    MyKibana.add_to_report(MyReport)
    MyReport.set_name("KIBANA_LOG_REPORT")
    MyReport.print_report(MyPars)

if __name__ == '__main__':
    main(sys.argv)

