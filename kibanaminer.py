# -----------------------------------------------------------
# J.Pianigiani, August 17 2022
# -----------------------------------------------------------
from itertools import count
import json
import requests
import os, sys
import argparse
import datetime
import string
import dateutil.parser as dparser
from report_library import parameters,report,menu
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
    Default = '\033[99m'


    def __init__(self, args):
        self.CONFIGFILENAME="configdata.json"
        self.QUERYFILENAME="query_generic.json"
        with open(self.CONFIGFILENAME,"r") as file2:
            configdata=json.load(file2)
        self.FieldsList=configdata["fields"]
        self.TwoLevelParseFields=configdata["two_level_parse"]
        self.elastic_url = configdata["endpoint"]["url"]
        self.session = requests.Session()
        self.session.verify = False
        self.session.proxies =configdata["endpoint"]["proxies"] 
        print(self.session.proxies)
        self.HEADERS = configdata["endpoint"]["headers"]
        self.query={}
        self.DEBUG=args.DEBUG
        if self.DEBUG:
            print("DEBUG Mode")

    def set_filter(self, args):

        self.localRegexDict={}
        if args.WORDS:
            Regexstring="("+"|".join(args.WORDS)+")"
            self.localRegexDict["WORDSREGEX"]=Regexstring

            self.localRegexDict["WORDS"]=re.compile(Regexstring)
            self.localRegexDict["WORDSFLAG"]=True
            if self.DEBUG: 
                print("Including only records matching the words:", self.FAIL,Regexstring, self.Yellow)

        else:
            self.localRegexDict["WORDSFLAG"]=False
        
        if args.EXCLUDEWORDS:
            Regexstring="("+"|".join(args.EXCLUDEWORDS)+")"
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
                QueryItem["range"]["@timestamp"]["gte"]=args.FROM
                QueryItem["range"]["@timestamp"]["lte"]=args.TO
        else :
                Tmp={
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
                Tmp["range"]["@timestamp"]["gte"]=args.FROM
                Tmp["range"]["@timestamp"]["lte"]=args.TO       
                filterlist.append(Tmp)

        for QueryItem in filterlist:
            #print(QueryItem)
            if "bool" in QueryItem.keys():
                AddWordFilter=False
        if AddWordFilter==False:
            print("UNHANDLED!")
            exit(-1)
        else :
                Tmp=        {
                            "bool": {
                                        "filter": [
     
                                        ]
                                    }
                            }

                #print("args.WORDS:",args.WORDS)
                count=0
                Tmp3=[]
                if args.WORDS:

                    for WordToAdd in args.WORDS:
                        
                        Tmp3.append({
                            "multi_match": {
                                "type": "best_fields",
                                "query": "FREE TEXT SEARCH",
                                "lenient": True
                                }
                            })
                        Tmp3[count]["multi_match"]["query"]=WordToAdd
                        Tmp["bool"]["filter"].append(Tmp3[count])
                        #print("Adding word : ",WordToAdd)
                        #print(Tmp3)
                        #print(Tmp)
                        count+=1


                count=0
                Tmp3=[]
                if args.EXCLUDEWORDS:

                    for WordToAdd in args.EXCLUDEWORDS:
                        Tmp3.append({
                                "bool": {
                                    "must_not": {
                                        "multi_match": 
                                            {
                                            "type": "best_fields",
                                            "query": "TEXTTOEXCLUDE",
                                            "lenient": True
                                        }
                                    }
                                }
                            })
                        Tmp3[count]["bool"]["must_not"]["multi_match"]["query"]=WordToAdd
                        Tmp["bool"]["filter"].append(Tmp3[count])
                        #print("Adding excludeword : ",WordToAdd)
                        #print(Tmp3)
                        #print(Tmp)
                        count+=1
                filterlist.append(Tmp)
        print(json.dumps(self.query, indent=5))


    def get_recursively(self, search_dict, field):
        """
        Takes a dict with nested lists and dicts,
        and searches all dicts for a key of the field
        provided.
        """
        fields_found = []    

        for key, value in search_dict.items():
            if key == field:
                fields_found.append(value)
            elif isinstance(value, dict):
                results = self.get_recursively(value, field)
                for result in results:
                    fields_found.append(result)


            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        more_results = self.get_recursively(item, field)
                        for another_result in more_results:
                            fields_found.append(another_result)

        return fields_found

    def get_data_from_kibana(self):
        self.request = self.session.get(self.elastic_url, headers=self.HEADERS, json=self.query)
        print("response code {}".format(self.request.status_code))
        self.queryresult=self.request.json()
        with open("kibanaminer.out","w") as file1:
            file1.write(json.dumps(self.queryresult,indent=10))

    def transform_data(self):
        self.count=0
        recno=0    
        self.transformed_data={}
        myindex=0
        for FIELD in self.FieldsList:
            for x in self.get_recursively(self.queryresult,FIELD):
                if FIELD=="time":
                    myindex=float(x)
                if recno==0:
                    #TMP[str(count)]={}
                    self.transformed_data[self.count]={}

                try:
                    #TMP[str(count)][FIELD]=x
                    self.transformed_data[self.count][FIELD]=x

                except:
                    pass

                    print("--------------------------------------------------------")
                    print(json.dumps(self.transformed_data,indent=4))
                    print("--------------------------------------------------------")
                    #print("JSON Keys of self.transformed_data: {:} \n {:}".format(len(self.transformed_data.keys()),self.transformed_data.keys()))
                    print("recno=",recno)
                    print("count=",self.count)
                    print("Field=",FIELD)
                    print("X=",x)

                    #exit(-1)
                    #src=input("Continue?")
                #print(TMP)
                self.count+=1
            recno+=1
            self.count=0     
        #print("--------------------------------------------------------")
        #print(json.dumps(self.transformed_data,indent=10))
        #exit(-1)

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
            print("--------------------------------------------")            
            print("TOTAL RECORDS FROM KIBANA: ", self.queryresult["hits"]["total"]["value"])
            print("--------------------------------------------")            

        for record in self.queryresult["hits"]["hits"]:
            if self.DEBUG:
                print(self.OKGREEN+"--------------------------------------------")            
                print("Record # ", self.count)
                print("--------------------------------------------"+self.Yellow)            
            #self.transformed_data[self.count]={}
            IncludeRecord=False
            ExcludeRecord=False
            temp_result={}
            for mykey in self.FieldsList:
                if mykey in record.keys():
                    root=record
                else:
                    root= record["_source"]
                stringvalue = root[mykey]
                #print("----------------------------")
                #print("stringvalue:")
                #print(stringvalue)
                #print("of type: ", type(stringvalue))
                try:
                    value=json.load (stringvalue.lower())
                    #print("DICT!:", value)
                except:
                    value=stringvalue.lower()


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
        with open("kibanaminer.short.out","w") as file1:
            file1.write(json.dumps(self.transformed_data,indent=10))


    def sort_by_timestamp(self):
        pass

    def add_to_report(self, reportobject):
        for item in self.transformed_data.keys():
            
            print("Item:", item,"\n",json.dumps(self.transformed_data[item],indent=5))

            reportobject.addemptyrecord()
            for field in self.FieldsList:
            #["time","timestamp","_index","host","ident","severity","message"]
                reportobject.UpdateLastRecordValueByKey(field,self.transformed_data[item][field])

    def interactive(self):
        #src= input("continue?")
        print(self.FAIL+"\t<CR>: Next\t-:Back\t<ESC> or q:Exit"+self.Yellow)
        #charlist={'q':0,'Q':0,'-':-1,'\n':1,' ':1,'/':2,chr(27):0,'2':100,'1':10}
        charlist={
            "q":{"value":0,"action":"exit"},
            "1":{"value":0,"action":"exit"},
            chr(27):{"value":0,"action":"exit"},
            "-":{"value":-1,"action":"delta"},
            '\n':{"value":1,"action":"delta"},
            chr(91)+chr(67):{"value":1,"action":"delta"},

            "1":{"value":10,"action":"delta"},
            "2":{"value":100,"action":"delta"}


        }

        ch=''
        action="delta"
        while ch not in charlist.keys():
            ch=getch.getche()
            print(ascii(ch))
        retval=charlist[ch]["value"]
        action= charlist[ch]["action"]

        return retval, action

    def scan_and_parse_messages(self, args,reportobject):
        mylist= list(self.transformed_data.keys())
        mylistlen=len(mylist)
        print(mylist)
        key=0
        #for key in self.transformed_data.keys():
        GoOn=True
        while GoOn:
            #print("key:",key, " len of keys:",mylistlen)
            #message=[ self.transformed_data[key]["_index"], self.transformed_data[key]["message"]]
            try:
                message=[]
                for field in self.TwoLevelParseFields :
                    #print("DEBUG: Adding ", field, " to message ",message, " from ",self.transformed_data[key] )
                    if field in self.transformed_data[key].keys():
                        message.append (self.transformed_data[key][field])
            except:
                print("scan_and_parse_messages: message:",message)
                print("scan_and_parse_messages: Field:",field)
                exit(-1)
            #print("MESSAGE:", message)
            print(self.Backg_Yellow+"____________ kibanaminer.py:scan_and_parse_messages__________"+self.Backg_Default)
            print("RECORD: {:}\n{:}\n".format(key,json.dumps(self.transformed_data[key],indent=5)))
            #print("Message:\n",message)
            #try:
            reportobject.message_parser(message)
            #except:
            #    print("kibanaminer.py:scan_and_parse_messages - error searching {:} in {:}".format(key,message))
            if args.INTERACTIVE:
                Delta, action=self.interactive()
                if Delta==0:
                    return 0
                key+=Delta
                key%= mylistlen
            else:
                key+=1
                if key>=mylistlen:
                    return True
            

def main(arguments):
    programname= arguments[0].split(".")[0]
    MyPars=parameters(programname)
    MyReport=report(MyPars)
    parser = argparse.ArgumentParser()
    CurrentTime = datetime.datetime.now()
    DefaultFromTime=CurrentTime-datetime.timedelta(hours=24)
    DefaultTo= CurrentTime.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    DefaultFrom= DefaultFromTime.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    parser.add_argument("-f","--FROM",help="Specify from when to start fetching logs (%Y-%m-%dT%H:%M:%S.000Z). If omitted=Now-1day", default=DefaultFrom, required=False)
    parser.add_argument("-t","--TO",help="Specify to when to fetch logs( %Y-%m-%dT%H:%M:%S.000Z). If omitted=Now", default=DefaultTo, required=False)
    parser.add_argument("-w","--WORDS", nargs='+', help="List of space-separated words to search in logs", required=False, type=str)
    parser.add_argument("-x","--EXCLUDEWORDS", nargs='+', help="List of space-separated words to EXCLUDE in logs", required=False, default=[], type=str)
    parser.add_argument("-i","--INTERACTIVE", help="If specified, interactive menu is presented after each record to navigate", action='store_true')
    #type=bool, default=False, required=False)
    parser.add_argument("-d","--DEBUG", help="If specified, DEBUG mode set to true", action='store_true')
    parser.add_argument("-r","--RECORDS", help="N. of hits returned by query, default=1000", type=int, default=1000, required=False)

    args=parser.parse_args()

    MyKibana=kibanaminer(args)
    MyKibana.set_filter(args)
    MyKibana.get_data_from_kibana()
    MyKibana.transform_data2(args)
    MyKibana.scan_and_parse_messages(args,MyReport)
    MyKibana.add_to_report(MyReport)
    MyReport.set_name("KIBANA_LOG_REPORT")
    MyReport.print_report(MyPars)

if __name__ == '__main__':
    main(sys.argv)

