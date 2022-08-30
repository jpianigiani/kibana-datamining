# -----------------------------------------------------------
# J.Pianigiani, August 17 2022
# -----------------------------------------------------------
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

# http://aop-kibana.poc.dcn.telekom.de:5601/app/kibana#/dev_tools/console?_g=(filters:!())


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
    Default = '\033[99m'


    def __init__(self):
        self.CONFIGFILENAME="configdata.json"
        self.QUERYFILENAME="query_generic.json"
        with open(self.CONFIGFILENAME,"r") as file2:
            configdata=json.load(file2)
        self.FieldsList=configdata["fields"]
        self.elastic_url = configdata["endpoint"]["url"]
        self.session = requests.Session()
        self.session.verify = False
        self.session.proxies =configdata["endpoint"]["proxies"] 
        print(self.session.proxies)
        self.HEADERS = configdata["endpoint"]["headers"]
        self.query={}

    def set_filter(self, args):

        self.localRegexDict={}
        if args.WORDS:
            self.localRegexDict["WORDS"]=re.compile(" ".join(args.WORDS))
            self.localRegexDict["WORDSFLAG"]=True

        else:
            self.localRegexDict["WORDSFLAG"]=False
        
        if args.EXCLUDEWORDS:
            self.localRegexDict["EXCLUDEWORDS"]=re.compile(" ".join(args.EXCLUDEWORDS))
            self.localRegexDict["EXCLUDEWORDSFLAG"]=True
        else:
            self.localRegexDict["EXCLUDEWORDSFLAG"]=False
        print("DEBUG: WORDSFLAG=",self.localRegexDict["WORDSFLAG"])
        print("DEBUG: EXCLUDEWORDSFLAG=",self.localRegexDict["EXCLUDEWORDSFLAG"])

        with open(self.QUERYFILENAME, "r") as file1:
                self.query = json.load(file1)
        filterlist= self.query["query"]["bool"]["filter"]
        AddTimeFilter=True
        AddWordFilter=True
        for QueryItem in filterlist:
            print(QueryItem)
            if "range" in QueryItem.keys():
                AddTimeFilter=False
                break

        if AddTimeFilter==False:
                print("range key present")
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

                print("args.WORDS:",args.WORDS)
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
                        print("Adding word : ",WordToAdd)
                        print(Tmp3)
                        print(Tmp)
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
                        print("Adding excludeword : ",WordToAdd)
                        print(Tmp3)
                        print(Tmp)
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
        count=0
        recno=0    
        self.transformed_data={}
        myindex=0
        for FIELD in self.FieldsList:
            for x in self.get_recursively(self.queryresult,FIELD):
                if FIELD=="time":
                    myindex=float(x)
                if recno==0:
                    #TMP[str(count)]={}
                    self.transformed_data[count]={}

                try:
                    #TMP[str(count)][FIELD]=x
                    self.transformed_data[count][FIELD]=x

                except:
                    pass

                    print("--------------------------------------------------------")
                    print(json.dumps(self.transformed_data,indent=4))
                    print("--------------------------------------------------------")
                    #print("JSON Keys of self.transformed_data: {:} \n {:}".format(len(self.transformed_data.keys()),self.transformed_data.keys()))
                    print("recno=",recno)
                    print("count=",count)
                    print("Field=",FIELD)
                    print("X=",x)

                    #exit(-1)
                    #src=input("Continue?")
                #print(TMP)
                count+=1
            recno+=1
            count=0     
        #print("--------------------------------------------------------")
        #print(json.dumps(self.transformed_data,indent=10))
        #exit(-1)

    def transform_data2(self, arguments):
        self.ExcludedCounter=0
        self.transformed_data={}
        count=0
        for record in self.queryresult["hits"]["hits"]:
            self.transformed_data[count]={}
            IncludeRecord=True
            ExcludeRecord=False
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
                    value=json.load (stringvalue)
                    #print("DICT!:", value)
                except:
                    value=stringvalue
                    

                if self.localRegexDict["EXCLUDEWORDSFLAG"]:
                    ExcludeWordsMatchResult=self.localRegexDict["EXCLUDEWORDS"].match(value)
                    if ExcludeWordsMatchResult:
                        ExcludeRecord=True
                        print(menu.FAIL+"\t\tValue: ", value, " ExcludeWordsMatchResult:",ExcludeWordsMatchResult,menu.YELLOW)

                if self.localRegexDict["WORDSFLAG"]:
                    WordsMatchResult=self.localRegexDict["WORDS"].match(value)
                    if WordsMatchResult:
                        IncludeRecord=True
                        print(menu.FAIL+"\t\tValue: ", value, " Wordsmatchresult:",WordsMatchResult,menu.YELLOW)


                if IncludeRecord or ExcludeRecord==False:
                
                    if isinstance(value,dict):
                        self.transformed_data[count][mykey]=json.dumps(value,indent=4)
                    else:
                        self.transformed_data[count][mykey]=value
                else:
                    self.ExcludedCounter+=1
                    print("\tExcluded records due to Preliminary Regex: {:}".format(self.ExcludedCounter))
            count+=1
        with open("kibanaminer.short.out","w") as file1:
            file1.write(json.dumps(self.transformed_data,indent=10))


    def sort_by_timestamp(self):
        pass

    def add_to_report(self, reportobject):
        for item in self.transformed_data.keys():
            print(json.dumps(self.transformed_data[item],indent=5))
            reportobject.addemptyrecord()
            for field in self.FieldsList:
            #["time","timestamp","_index","host","ident","severity","message"]
                reportobject.UpdateLastRecordValueByKey(field,self.transformed_data[item][field])

    def interactive(self):
        #src= input("continue?")
        print(self.FAIL+"\t<CR>: Next\t-:Back\t<ESC> or q:Exit"+self.Yellow)
        charlist={'q':0,'Q':0,'-':-1,'\n':1,' ':1,'/':2,chr(27):0,'2':100,'1':10}
        ch=''
        while ch not in charlist.keys():
            ch=getch.getche()
            print(ascii(ch))
        retval=charlist[ch]

        if retval==0:
            return retval
        else:
            return retval

    def parse_messages(self, args,reportobject):

        mylist= list(self.transformed_data.keys())
        mylistlen=len(mylist)
        print(mylist)
        key=0
        #for key in self.transformed_data.keys():
        GoOn=True
        while GoOn:
            print("key:",key, " len of keys:",mylistlen)
            message=[ self.transformed_data[key]["_index"], self.transformed_data[key]["message"]]
            print("____________ kibanaminer.py:parse_messages__________")
            print("RECORD: {:}\n{:}\n".format(key,json.dumps(self.transformed_data[key],indent=5)))
            #print("Message:\n",message)
            #try:
            reportobject.message_parser(message)
            #except:
            #    print("kibanaminer.py:parse_messages - error searching {:} in {:}".format(key,message))
            if args.INTERACTIVE:
                Delta=self.interactive()
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
    print(programname)
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
    args=parser.parse_args()

    MyKibana=kibanaminer()
    MyKibana.set_filter(args)
    MyKibana.get_data_from_kibana()
    MyKibana.transform_data2(args)
    MyKibana.parse_messages(args,MyReport)
    MyKibana.add_to_report(MyReport)
    MyReport.set_name("KIBANA_LOG_REPORT")
    
    MyReport.print_report(MyPars)

if __name__ == '__main__':
    main(sys.argv)

