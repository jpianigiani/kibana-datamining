# Author Jacopo Pianigiani jacopopianigiani@juniper.net
# Written in 2022

import json
import string
import sys
import glob
import os
import math
import re
from datetime import datetime
import traceback
try: 
    from aop_logger import aop_logger
except:
    print("No aop_logger module to import")
#from aop_logger import aop_logger



# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
#                           CLASS :     PARAMETERS
# -------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------
class parameters:
    # 
    # -------------------------------------------------------------------------------------------------------------------------
    # GLOBAL DICTIONARIES: these are used to store command line arguments values or user input values (so that the behavior is consistent between User interactive mode and CLI mode)

    PATHFORAPPLICATIONCONFIGDATA='./'
    APPLICATION = 'resource-analysis'

    APPLICATIONCONFIG_DICTIONARY={}
    MODE_OF_OPT_OPS = 0
    paramsdict={}
    paramslist=[]
    ERROR_REPORT=[]    
    ERROR_DATA=[]
    
    # -------------------------------------------------------------------------------------------------------------------------
    # FORMULAS FOR DISTANCE CALCULATION FROM TARGET
    # -------------------------------------------------------------------------------------------------------------------------

    # , 'abs(currentvalue-average)',  '(currentvalue-minimum)**4']
    #metricformulas = ['(currentvalue-average)**2']
    # -------------------------------------------------------------------------------------------------------------------------
    NO_OPTIMIZATION = 0
    OPTIMIZE_BY_CALC = 1
    OPTIMIZE_BY_FILE = 2

    def __init__(self, myApplicationName=APPLICATION):
        
        modulename="aop_logger"
        if modulename not in sys.modules:
            self.AOP_LOGGER_ENABLED=False
        else:
            self.AOP_LOGGER_ENABLED=True
        self.myApplicationName=myApplicationName
        CONFIGFILENAME=myApplicationName+".json"
        print("opening config file : ",CONFIGFILENAME)
        ERRORFILENAME=myApplicationName+"-errors.json"
        self.SYSLOGFILE=myApplicationName+".log"
        now = datetime.now()  # current date and time
        date_time = now.strftime("%d/%m/%Y %H:%M:%S")
        #date_time = now.strftime("%d/%m/%Y")
        self.paramsdict["TIMESTAMP"] = date_time
        TMPJSON=[]
        self.DSTSITES = []
        self.screenrows, self.screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh = int(self.screencolumns)
        self.ColorsList =(menu.OKBLUE,menu.OKCYAN,menu.OKGREEN,menu.WARNING,menu.FAIL,menu.White,menu.Yellow,menu.Magenta,menu.Grey) 
        self.ERROR_REPORT=[]
        self.Stringa0="{0: ^"+str(self.ScreenWitdh)+"}"
        self.FOREANDBACKGROUND='\033[38;5;{:d};48;5;{:d}m'
        self.RESETCOLOR='\033[0m'
        #-------------------------------------------------------------------------------------------------------------------
        try:

            with open(self.PATHFORAPPLICATIONCONFIGDATA+CONFIGFILENAME,'r') as ConfigFile:
                try:
                    TMPJSON = json.load(ConfigFile)
                except:
                    traceback.print_exc(limit=None, file=None, chain=True)
                    print(" CRITICAL! : object class PARAMETERS, __init__ found JSON syntax error in  {:}".format(self.PATHFORAPPLICATIONCONFIGDATA+CONFIGFILENAME))
                    exit(-1)
            self.APPLICATIONCONFIG_DICTIONARY=dict(TMPJSON)
        #-------------------------------------------------------------------------------------------------------------------
            self.PATHFOROUTPUTREPORTS=self.APPLICATIONCONFIG_DICTIONARY["Files"]["PathForOutputReports"]
        #-------------------------------------------------------------------------------------------------------------------
            self.paramsdict = self.APPLICATIONCONFIG_DICTIONARY["Application_Parameters"]
            self.paramslist=list(self.APPLICATIONCONFIG_DICTIONARY["User_CLI_Visible_Parameters"])
        #-------------------------------------------------------------------------------------------------------------------
        
        except:
            traceback.print_exc(limit=None, file=None, chain=True)
            #-------------------------------------------------------------------------------------------------------------------
            print("#-------------------------------------------------------------------------------------------------------------------")
            print(" CRITICAL! : object class PARAMETERS, __init__ did not find the application configuration file {:}".format(self.PATHFORAPPLICATIONCONFIGDATA+CONFIGFILENAME))
            print("\t Files {:} and  {:} must be , from thedirectory as python main executable, as follows: {:}".format(CONFIGFILENAME, ERRORFILENAME,self.PATHFORAPPLICATIONCONFIGDATA))
            print("#-------------------------------------------------------------------------------------------------------------------")
            exit(-1)
        #-------------------------------------------------------------------------------------------------------------------
        try:
            with open(self.PATHFORAPPLICATIONCONFIGDATA+ERRORFILENAME,'r') as ConfigFile:
                self.ERROR_DICTIONARY = json.load(ConfigFile)
        except:
            traceback.print_exc(limit=None, file=None, chain=True)
            print("#-------------------------------------------------------------------------------------------------------------------")
            print(" CRITICAL! : object class PARAMETERS, __init__ did not find the application errors dictionary  file {:}".format(self.PATHFORAPPLICATIONCONFIGDATA+ERRORFILENAME))
            print("\t Files {:} and  {:} must be , from the directory as python main executable, as follows: {:}".format(CONFIGFILENAME, ERRORFILENAME,self.PATHFORAPPLICATIONCONFIGDATA))
            print("#-------------------------------------------------------------------------------------------------------------------")
            exit(-1)
         
        self.DEBUG=self.APPLICATIONCONFIG_DICTIONARY["Application_Parameters"]["DEBUG"]
        #-------------------------------------------------------------------------------------------------------------------
        try:
            if self.AOP_LOGGER_ENABLED:
                mysyslog=aop_logger(3,self.SYSLOGFILE)
                myloghandler=mysyslog.syslog_handler(
                        address= (self.APPLICATIONCONFIG_DICTIONARY["syslog"]["Target"],
                        self.APPLICATIONCONFIG_DICTIONARY["syslog"]["Port"]))
                self.logger=mysyslog.logger
        except NameError as Err:
            print("AOP-LOGGER disabled")

        #-------------------------------------------------------------------------------------------------------------------
    def get_logger(self):
        return self.logger



    def get_configdata_dictionary(self):
        return self.APPLICATIONCONFIG_DICTIONARY

    def set(self, key, value):
        self.paramsdict[key] = value
        return value

    def get(self, key):
        return self.paramsdict[key]

    def is_silentmode(self):
        return self.paramsdict["SILENTMODE"]
    # -----------------------------------
    def get_param_value(self, name):
        if name in self.paramsdict.keys():
            return self.paramsdict[name]
        else:
            return "**"
    # -----------------------------------

    # -----------------------------------
    def show_cli_command(self):
        MyLine = menu.OKGREEN+'{0:_^'+str(self.ScreenWitdh)+'}'
        print(MyLine.format('LIST OF PARAMETER ARGUMENTS'))
        print(json.dumps(self.paramsdict,indent=40))
        # PRINT CLI COMMAND AND PARAMETERS USED
        CMD = "python3 <appname>.py"
        for x in self.paramsdict:
            if x in self.paramslist:
                if type(x) == list:
                    l = len(x)
                    CMD += "{}=".format(x)
                    for x2 in x:
                        CMD += "{}".format(x2)
                        if x2 != x[l]:
                            CMD += ","
                else:
                    CMD += " {}={} ".format(x, self.paramsdict[x])

        CMD2 = CMD.replace("[", "")
        CMD3 = CMD2.replace("]", "")
        CMD4 = CMD3.replace(", ", ",")
        print(CMD4)
        return True
        
    def SuffixToShortDate(self,suffix):
        retval =suffix[6:8]+"-"+suffix[4:6]+"-"+suffix[0:4]
        return retval

    def SuffixToYYMMDDDateValue(self,suffix):
        retval =int(suffix[0:4]+suffix[4:6]+suffix[6:8])
        return retval
# --------------------EXTRACTS SITENAME FROM SUFFISSO note : STG810 specific parsing
    def parse_suffisso(self, suffisso):
        if len(suffisso) == 20:
            # NOTE: STG810 does not show stg810 in the suffix as the cc-jumphost hostname is configured wrongly
            sitename= suffisso[14:]
            retval=sitename.lower()
        else:
            sitename= "stg810"
            retval=sitename.lower()
        return retval
    
    def cast_error(self,ErrorCode, AddlData):
        NEWRECORD=[]
        a = str(self.__class__)
        #traceback.print_exc(limit=None, file=None, chain=True)
        #ErrorObjectClass= a.replace("'",'').replace("<",'').replace(">","").replace("class ","")

        ErrorInfo=self.ERROR_DICTIONARY[ErrorCode]
        #print(json.dumps(ErrorInfo,indent=30))
        ErrorObjectClass=ErrorInfo["Class"]
        SrcSuffix=self.get_param_value("SOURCE_SITE_SUFFIX")
        SiteName= self.parse_suffisso(SrcSuffix)
        if ErrorInfo["Level"]in self.APPLICATIONCONFIG_DICTIONARY["syslog"]["ErrorsToReport"]:
            NEWRECORD.append(SrcSuffix[0:8])
            NEWRECORD.append(SiteName)
            NEWRECORD.append(ErrorInfo["Level"])
            NEWRECORD.append(ErrorObjectClass)
            NEWRECORD.append(ErrorCode)
            NEWRECORD.append(ErrorInfo["Synopsis"])
            NEWRECORD.append(AddlData)
            #NEWRECORD.append(ErrorInfo)

            try:
                if self.AOP_LOGGER_ENABLED:
                    syslogstring="Timestamp: {:9s} Site: {:12s} ErrCode: {:5s} Class:{:30s} Synopsis:{:60s}: {:120s}".format(SrcSuffix[0:8],
                                SiteName,ErrorCode,ErrorObjectClass,ErrorInfo["Synopsis"],AddlData)
                    if ErrorInfo["Level"]=="CRITICAL":
                        self.logger.critical(syslogstring)
                    elif ErrorInfo["Level"]=="ERROR":
                        self.logger.error(syslogstring)
                    elif ErrorInfo["Level"]=="WARNING":
                        self.logger.warning(syslogstring)
            except NameError as Err:
                pass
            self.ERROR_REPORT.append(NEWRECORD)
        
        

        actions = ErrorInfo["AfterErrorExecution"]
        for Item in actions:
            print("cast_error")
            print(ErrorCode)
            print(NEWRECORD)
            print(AddlData)
            print(Item)
            eval(Item)


# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
#                           CLASS :     REPORT
# -------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------
class report():

    Report = []
    ReportTotalUsage = []
    #Select RGB foreground color

    def __init__(self,params, CustomReportTypePrefix=None):
        #super().__init__()
        self.Report = []
        if CustomReportTypePrefix:
            TypePrefix=CustomReportTypePrefix+"_"
        else:
            TypePrefix=""
        self.ReportType=TypePrefix+self.get_reporttype()
        self.State=''
        self.KEYS_KEYNAME="_KEYS"
        self.SORTINGKEYS_KEYNAME="_SORTING_KEYS"
        self.MULTILINEKEYS_KEYNAME="_MULTILINE_KEYS"
        self.color=menu.Yellow
        self.ReportTotalUsage = []
        self.ScreenWidth=params.ScreenWitdh
        self.PARAMS = params
        self.name=str(self.__class__).replace("'",'').replace("<",'').replace(">","").replace("class ","") + hex(id(self))
        self.Parameters_Configdata=params.APPLICATIONCONFIG_DICTIONARY

        self.ReportsNamesAndData = self.Parameters_Configdata["ReportsSettings"]
        self.FIELDLENGTHS= self.Parameters_Configdata["FieldLenghts"]
        self.FIELDLISTS= self.Parameters_Configdata["FieldLists"]
        #print(json.dumps(params.APPLICATIONCONFIG_DICTIONARY,indent=22))
        self.FIELDTRANSFORMS=self.Parameters_Configdata["FieldTransforms"]
        self.FILESSTRUCTURE =self.Parameters_Configdata["Files"]

        self.REPORTFIELDGROUP =self.Parameters_Configdata["Reports_Keys"]
        self.FIELDTRANSFORMSATTRIBUTES=self.Parameters_Configdata["FieldTransformsAttributes"]
        self.myRegexDict= {}
        self.compile_regexes()
        self.create_colorslist()


    def create_colorslist(self):
        def colorcompile(stringa, mytuple):
            return stringa.format(mytuple[0],mytuple[1])

        self.FOREANDBACKGROUND='\033[38;5;{:d};48;5;{:d}m'
        self.FOREGROUND='\033[38;2;{:d};{:d};{:d}m'
        self.BACKGROUND='\033[48;2;{:d};{:d};{:d}m'     #Select RGB background color
        self.RESET='\033[0m'

        self.Colorset={}
        self.Colorset["NormalList"]=[]
        self.Colorset["ReverseList"]=[]

        
        #https://i.stack.imgur.com/KTSQa.png
        self.Colorset["ReverseList"]=[]
        for BACKG in range(164,195,2):
            self.Colorset["ReverseList"].append(colorcompile(self.FOREANDBACKGROUND,(0,BACKG)))
            #+self.BACKGROUND.format(self.Colorset["BASE"]["BLACK"][0],self.Colorset["BASE"]["BLACK"][1],self.Colorset["BASE"]["BLACK"][2]))
        self.Colorset["NormalList"]=[]
        for FOREG in range(164,195,2):
            self.Colorset["NormalList"].append(colorcompile(self.FOREANDBACKGROUND,(FOREG,0)))


    def compile_regexes(self):
        self.myRegexDict={}
        for GroupName in self.FIELDTRANSFORMSATTRIBUTES.keys():
            self.myRegexDict[GroupName]={}
            for RegexListName in self.FIELDTRANSFORMSATTRIBUTES[GroupName].keys():
                for RegexItem in self.FIELDTRANSFORMSATTRIBUTES[GroupName][RegexListName]:
                    #print("Compiling Group:",GroupName,", regexlist ",RegexListName," RegexItem:",RegexItem)
                    CompiledRegex=re.compile(RegexItem)
                    self.myRegexDict[GroupName][RegexListName]=[]
                    self.myRegexDict[GroupName][RegexListName].append(CompiledRegex)
        
    def get_recursively(self,search_dict, field):
        if isinstance(search_dict, dict):
            if field in search_dict:
                return search_dict[field]
            for key in search_dict:
                item = self.get_recursively(search_dict[key], field)
                if item is not None:
                    return item
        elif isinstance(search_dict, list):
            for element in search_dict:
                item = self.get_recursively(element, field)
                if item is not None:
                    return item
        return None


    def get_regex(self,key, group,  subgroup=None):
        root1=self.myRegexDict
        root2=self.FIELDTRANSFORMSATTRIBUTES
        if subgroup is None:
            try:
                return root1[group][key],root2[group][key]
            except:

                exit(-1)
        else:
            return root1[group][subgroup][key],root2[group][subgroup][key]



    def get_reporttype(self,customname=""):
        if len(customname)==0:
            MyClass= str(self.__class__).replace("<","").replace(">","").replace("'","")
            retval=MyClass.split(".")[1].upper()
        else:
            retval=customname
        return retval

    def ClearData(self):      
        self.Report = []
        self.State=''
        self.ReportTotalUsage = []

    def set_name(self,myname):
        self.name=myname.upper()
        self.ReportFile = open(self.FILESSTRUCTURE["PathForOutputReports"]+"/"+self.name, 'w')

    def set_state(self,mystatus):
        self.State=mystatus.upper()
        self.write_line_to_file(mystatus)

    def write_line_to_file(self,line):
        try:
            self.ReportFile.write(line+"\n")
        except:
            self.PARAMS.cast_error("00005","line:"+line)

    def get_keys(self):
        try:
            return self.REPORTFIELDGROUP[self.ReportType+self.KEYS_KEYNAME]
        except:
            print("ERROR: get_keys: REPORTTYPE=",self.ReportType)
            self.PARAMS.cast_error( "00007","get_keys :{:}".format(self.ReportType+self.KEYS_KEYNAME))
        

    def get_sorting_keys(self):
        try:
            return self.REPORTFIELDGROUP[self.ReportType+self.SORTINGKEYS_KEYNAME]
        except:
            self.PARAMS.cast_error( "00006","get_sorting_keys: :{:}".format(self.ReportType+self.SORTINGKEYS_KEYNAME))

    def get_multiline_keys(self):
        try:
            return self.REPORTFIELDGROUP[self.ReportType+self.MULTILINEKEYS_KEYNAME]
        except:
            return ["0"]

    def UpdateLastRecordValueByKey(self, mykey, value):
        if mykey is None:
            print("UpdateLastRecordValueByKey : error : key is null") 
            exit(-1)
        record= self.Report[len(self.Report)-1]
        if mykey in self.FIELDLISTS.keys():
            if type(value)==list:
                for x in value:
                    record[self.get_keys().index(mykey)].append(x)
            else:
                record[self.get_keys().index(mykey)]=value

        else:
            #try:
            record[self.get_keys().index(mykey)]=value
            #except:
            #    print("ERROR IN UpdateLastRecordValueByKey")
            #    print("Report: {:} of type {:}",self.name,self.ReportType)
            #    print("Current keys:",self.get_keys())
            #    print("Searching key :",mykey)
            #    exit(-1)

    def FindRecordByKeyValue(self, mykey, value):
        MyFieldIndex=self.get_keys().index(mykey)
        for x in self.Report:
            if x[MyFieldIndex]==value:
                return x  
        return []        

    def AppendRecordToReport(self, newrecord):
        self.Report.append(newrecord)

    def length(self):
        return len(self.Report)

    def keys_length(self):
        return len(self.get_keys())

    def get_fieldlength(self,key):
        if key in self.FIELDLENGTHS:
            return self.FIELDLENGTHS[key]
        else:
            return self.FIELDLENGTHS["default"]

    def addemptyrecord(self):
        myrecord=[]
        for mykey in self.get_keys():
            if mykey in self.FIELDLISTS.keys():
                value=[]
            else:
                value=""
            myrecord.append(value)
        self.Report.append(myrecord)
        return self.Report[len(self.Report)-1]

    def get_column_by_key(self,mykey):
        Index=self.get_keys().index(mykey)
        retval=[row[Index] for row in self.Report]
        return retval




#---------------------------------------------------
#   Receives a Report Record, produces as return value a 2D Array containing one record per Line to be printed with wrapping of text beyond FieldLength
#---------------------------------------------------
    def LineWrapper(self, record):
        var_Keys=self.get_keys()
        Lines=[[]]
        MaxRows=1024
        Lines=[['' for j in range(len(var_Keys) )] for i in range(MaxRows)]
        if record is None:
            print("DEBUG: LineWrapper : record is NONE")
            exit(-1)
        MaxRows=0
        try: #CHANGETHIS
            myunwrappedline=''
            for ReportKeyItem in var_Keys:
                RecordEntryIndex =var_Keys.index(ReportKeyItem)
                var_FieldLen = self.get_fieldlength(ReportKeyItem)
                var_RecordEntry= record[RecordEntryIndex]
                if var_RecordEntry is None:
                    print("DEBUG LineWrapper: Field {:} is none \nfor record: ".format(ReportKeyItem,record))
                    exit(-1)  
                if type(var_RecordEntry)== list:
                    var_Entry=""
                    for ListItem in var_RecordEntry:
                        var_Entry+=ListItem
                else:
                    var_Entry=var_RecordEntry
                var_RecordEntryLen = len(var_Entry)
                
                stringa1="{:"+str( var_FieldLen  )+"s} |"
                myunwrappedline+=stringa1.format(var_Entry)  

                RowsValue = math.ceil(var_RecordEntryLen/var_FieldLen)
                if RowsValue>MaxRows:
                    MaxRows=RowsValue
                if RowsValue==0:
                    #print("DEBUG LineWrapper: Field {:} has Rowsvalue={:} \nfor record: ".format(ReportKeyItem,RowsValue,record))
                    RowsValue=1
                    Lines[0][RecordEntryIndex]=""
                    #exit(-1)    
                else:
                    for NofLinesPerRecEntry in range(RowsValue):
                        stringa_start = NofLinesPerRecEntry*var_FieldLen
                        if (var_RecordEntryLen> stringa_start+ var_FieldLen  ):
                            stringa_end = (1+NofLinesPerRecEntry)*var_FieldLen
                        else:
                            stringa_end =  var_RecordEntryLen
                        try:
                            newItem=var_Entry[stringa_start:stringa_end]
                        except:
                            print("DEBUG: Error in LineWrapper : ReportKeyItem : {:}, Var_Entry={:}".format(ReportKeyItem,var_Entry))
                            exit(-1)
                        Lines[NofLinesPerRecEntry][RecordEntryIndex]=newItem
                    

            retval=[]
            for i in range(MaxRows):
                myline=''
                for j in range(len(var_Keys)):
                    length=self.get_fieldlength(var_Keys[j])
                    stringa1="{:"+str( length  )+"s} |"
                    myline+=stringa1.format(Lines[i][j])  

                retval.append(myline)

            return retval,myunwrappedline


        except:
            traceback.print_exc(limit=None, file=None, chain=True)
            print("Record:", record)
            print("ReportKeyItem=",ReportKeyItem)
            self.PARAMS.cast_error("00009","Record:"+str(record))
            exit(-1)


#---------------------------------------------------
#   Receives a Report Record, produces as return value a 2D Array containing one record per Line to be printed with wrapping of text beyond FieldLength
#---------------------------------------------------
    def LineWrapper_V2(self, record):

        if record is None:
            print("DEBUG: LineWrapper : record is NONE")
            exit(-1)
        

        #try: #CHANGETHIS

        ListOfMultilineKeys=self.get_multiline_keys()
        if ListOfMultilineKeys==["0"]:
            self.MultiLineFlag=False
        else:
            self.MultiLineFlag=True
        LastMultilineKey=str(len(ListOfMultilineKeys)-1)

        Lines=[[]]
        #print("DEBUG - Wrapperv2 : FIELDLENGTHS")
        #print(json.dumps(self.FIELDLENGTHS ,indent=4))
        #print("DEBUG - Wrapperv2 : FIELDLISTS")
        #print(json.dumps(self.FIELDLISTS,indent=4))
        myunwrappedline=''
        retval=[]
        #print(json.dumps(ListOfMultilineKeys, indent=4))
        for MultiLineRowIndexString in ListOfMultilineKeys:
            #print("________________________________ _________________ __________________________")
            #print("DEBUG MultiLineRowIndexString:",MultiLineRowIndexString)
            var_TotalKeys=self.get_keys()
            MaxRows=256
            MaxSizeofRows=MaxRows
            Lines=[['' for j in range(len(var_TotalKeys) )] for i in range(MaxRows*len(ListOfMultilineKeys))] 
            if self.MultiLineFlag:
                var_LineKeys=self.get_multiline_keys()[MultiLineRowIndexString]
            else:
                var_LineKeys=self.get_keys()

            MultiLineRowIndex=int(MultiLineRowIndexString)
            #print("DEBUG - v2 - ",MultiLineRowIndex, "....",var_Keys)
            MaxRows=0
            for ReportKeyItem in var_LineKeys:
                RecordEntryIndex =var_TotalKeys.index(ReportKeyItem)
                TableEntryIndex=var_LineKeys.index(ReportKeyItem)

                var_FieldLen = self.get_fieldlength(ReportKeyItem)
                var_RecordEntry= record[RecordEntryIndex]

                if var_RecordEntry is None:
                    print("DEBUG LineWrapper: Field {:} is none \nfor record:-->\n{:}<--\n".format(ReportKeyItem,record))
                    exit(-1)  

                #if type(var_RecordEntry)== list:
                #    var_Entry=""
                #    for ListItem in var_RecordEntry:
                #        var_Entry+=ListItem
                #else:
                #    var_Entry=var_RecordEntry
                
                var_Entry="".join(var_RecordEntry)
                var_RecordEntryLen = len(var_Entry)
                #print("DEBUG: var_RecordEntry:",var_RecordEntry," var_Entry:-->",var_Entry,"<--",type(var_RecordEntry)," len of:", var_RecordEntryLen)
                
                stringa1="{:"+str( var_FieldLen  )+"s} |"
                try:
                    myunwrappedline+=stringa1.format(var_Entry)  
                except:
                    print("var_Entry:",var_Entry)
                    print("myunwrappedline:",myunwrappedline)
                    print("stringa1:",stringa1)
                    print("var_RecordEntry:",var_RecordEntry)
                    print("ReportKeyItem:",ReportKeyItem)
                    exit(1)
                # This section produces a 2D array, where each line contains the part of each record in each line
                RowsValue = math.ceil(var_RecordEntryLen/var_FieldLen)
                #print("DEBUG: RowsValue:",RowsValue, " var_RecordEntryLen:", var_RecordEntryLen," var_FieldLen:",var_FieldLen)
                if RowsValue>MaxRows:
                    MaxRows=RowsValue

                if RowsValue==0:
                    #print("DEBUG LineWrapper: Field {:} has Rowsvalue={:} \nfor record: ".format(ReportKeyItem,RowsValue,record))
                    RowsValue=1
                    Lines[0][TableEntryIndex]=""
                    #exit(-1)    
                else:
                    for NofLinesPerRecEntry in range(min(RowsValue, MaxSizeofRows)):
                        stringa_start = NofLinesPerRecEntry*var_FieldLen
                        if (var_RecordEntryLen> stringa_start+ var_FieldLen  ):
                            stringa_end = (1+NofLinesPerRecEntry)*var_FieldLen
                        else:
                            stringa_end =  var_RecordEntryLen
                        try:
                            newItem=var_Entry[stringa_start:stringa_end]
                        except:
                            print("DEBUG: Error in LineWrapper : ReportKeyItem : {:}, Var_Entry={:}".format(ReportKeyItem,var_Entry))
                            exit(-1)
                        Lines[NofLinesPerRecEntry][TableEntryIndex]=newItem
                    
                if MultiLineRowIndex==1 and False :
                    print("DEBUG - Linewrapperv2 - \nReportKeyIem:",ReportKeyItem, " in var_Linekeys:",var_LineKeys,"\nRecordEntryIndex :",RecordEntryIndex, " TableEntryIndex:",TableEntryIndex)
                    print("var_RecordEntry:",var_RecordEntry)
                    print("MaxRows:",MaxRows)
                    print("var_Entry:",var_Entry)
                    print("Lines:\n",Lines)

            if MaxRows>MaxSizeofRows:
                print(self.FOREANDBACKGROUND.format(255,9)+ "ERROR: Exceeding {:} rows for this record".format(MaxSizeofRows)+self.RESET)
            for i in range(min(MaxRows,MaxSizeofRows)):
                myline=''
                for j in range(len(var_LineKeys)):
                    length=self.get_fieldlength(var_LineKeys[j])
                    stringa1="{:"+str( length  )+"s} |"
                    stringa2=stringa1.format(Lines[i][j])
                    myline+=stringa2  
            
                retval.append(myline)
            #string1="_"*LineLenTotal
            #print("LastMultilineKey:",LastMultilineKey," LastMultilineKey:",LastMultilineKey)
            if MultiLineRowIndexString==LastMultilineKey:
                char="-"
            else:
                char="."
            string1=char*self.ScreenWidth
            if self.MultiLineFlag:
                retval.append(string1)
        return retval,myunwrappedline

            
        #except:
        #    traceback.print_exc(limit=None, file=None, chain=True)
        #    print("Record:", record)
        #    print("ReportKeyItem=",ReportKeyItem)
        #    self.PARAMS.cast_error("00009","Record:"+str(record))
        #    exit(-1)




#---------------------------------------------------
#   Receives a Report Record, produces a 1D record[] after applying Transforms to each entry in accordance to .json file of application configuration
#---------------------------------------------------
    def Record_ApplyTransforms(self,record):
        reportkeys=self.get_keys()
        NewRecord=[]
        currentrecord={}

        for row_itemnumber in range(self.keys_length()):
            # Fetches each item in the report row into initialvalue and gets what type it is, and what's the length of the output record (FIELDLENGTH)
            initialvalue = record[row_itemnumber]
            mytype = type(initialvalue)
            key=reportkeys[row_itemnumber]
            currentrecord[key]=record[row_itemnumber]
            columnname = reportkeys[row_itemnumber]
            length= self.get_fieldlength(columnname)
            #length = self.FIELDLENGTHS[columnname]
            FormatString_SingleValue="{:"+str( length)+"s}"
            try:
                transform = self.FIELDTRANSFORMS[columnname]
            except:
                transform = 'value'
            try:
                if mytype == list:
                    if columnname not in self.FIELDLISTS:
                        print("ERROR 04 - ApplyTransforms")
                        print("Record_ApplyTransforms: ERROR 04 START - \nMost likely FIELD is a list but it is not present in the application config JSON in the FIELDSLIST, so it is not classified neither list nor else\n")
                        print("transform=",transform)
                        print("column:",columnname)
                        print("currentrecord[key]:",currentrecord[key])
                        
                        exit(-1)
                    ListItemLen =self.FIELDLISTS[columnname]
                    FormatString_ListItemField ="{:"+str( ListItemLen)+"s}"
                    NewRecordListEntry=[]
                    for RecordEntry in initialvalue:
                        try:
                            value = FormatString_ListItemField.format(str(RecordEntry))
                            TransformedValue = eval(transform)
                            NewRecordListEntry.append(TransformedValue)

                        except:
                            traceback.print_exc(limit=None, file=None, chain=True)

                            ErrString="ApplyTransforms: item RecordEntry={:},transform={:}".format(RecordEntry,transform)
                            self.PARAMS.cast_error("00010",ErrString)
                    NewRecord.append(NewRecordListEntry)
                    
                else:
                    value = str(initialvalue)
                    NewRecord.append(FormatString_SingleValue.format(eval(transform)))

            except:
                #traceback.print_exc(limit=None, file=None, chain=True)
                print("######################################")
                print("Record_ApplyTransforms: ERROR 04 START - \nMost likely FIELD is a list but it is not present in the application config JSON in the FIELDSLIST, so it is not classified neither list nor else\n")
                print("transform function =",transform)
                print("column:",columnname)
                print("Field to apply is: {:} of type {:} and value {:} of type {;}".format(key,mytype,value,type))
                print("Record: {:} , current field index {:}\n".format(record,row_itemnumber))
                #print("Result of applying transform ")
                #eval(transform)
                print("Record_ApplyTransforms: ERROR 04 - END")
                print("######################################")

                exit(-1)

        return NewRecord


  # ---------------------------------
    # Print  report Keys header - using Text Wrapping
    # ---------------------------------   
    def print_report_line(self, pars,record, applytransforms):
            color=self.color
            NewRecord=[]
            NewLines=[[]]
            if applytransforms:
                NewRecord=self.Record_ApplyTransforms(record)
            else:
                NewRecord=record
                #print("DEBUG print_report_line")
                #print("record:")
                #print(NewRecord)
                #print("Report name",self.name)
            NewLines,UnWrappedline=self.LineWrapper_V2(NewRecord)

            print_on_screen=self.ReportType not in pars.APPLICATIONCONFIG_DICTIONARY["ReportsSettings"]["ReportTypesNotToBePrintedOnScreen"]
            wrap_line_on_file=pars.APPLICATIONCONFIG_DICTIONARY["ReportsSettings"]["WrapLinesWhenWritingToFiles"]

            for myline in NewLines:
                    if print_on_screen:
                        print("{:}".format(color+myline))
                        print
                    if wrap_line_on_file:
                        self.write_line_to_file("{:s}".format(myline))
            if wrap_line_on_file==False:
                self.write_line_to_file("{:s}".format(UnWrappedline))

    # ---------------------------------
    # Print a report ARRAY (list of lists), line by line  - Includes Text Wrapping
    # ---------------------------------
    def print_report(self, pars):
        # REPORT HEADER
        color=self.color
        MyLine = color+'{0:_^'+str(pars.ScreenWitdh)+'}'
        print(MyLine.format(self.name))
        self.write_line_to_file(MyLine.format(self.name)+"\n")
        print(MyLine.format(self.State))
        self.write_line_to_file(MyLine.format(self.State)+"\n")

        #PRINT KEYS HEADER
        self.print_report_line(pars,self.get_keys(), False)

        # PRINT THE REPORT LINE BY LINE
        NewRecord=[]
        reportkeys=self.get_keys()
        for record in self.Report:
            self.print_report_line(pars,record,True)

        return -1

    # ---------------------------------
    # SORT SOURCE REPORT IN ACCORDANCE TO SORTING KEYS
    # ---------------------------------
    def sort_report(self, sortkeys):
        #try:
            reportkeys = self.get_keys()
            mykeys = []
            myfunc = ''
            for m in sortkeys:
                val = reportkeys.index(m)
                mykeys.append('x['+str(val)+']')
            myfunc = ",".join(mykeys)


            self.Report.sort(key=lambda x: eval(myfunc))
        #except:
        #    print("SORT_REPORT: \nSorting Keys = {:} \nReport Keys = {:}\n".format(
        #        sortkeys, reportkeys))
        #    return -1

    


    def split_string(self, inputstring, resulttype,join=[],joiner='-'):
        CompiledRegexList,UncompiledRegexList = self.get_regex(resulttype,"split_string")
        for Regex in CompiledRegexList:
            Result= Regex.match(inputstring)
            if Result:
                #print(vmname,resulttype,Result, "-".join (Result.groups()))
                if len(join)==0:
                    return joiner.join (Result.groups())
                else:
                    resstring=""
                    for groupid in join:
                        resstring=joiner.join(Result.groups(groupid))
                    return resstring 
            else:
                #print("split_string : parsed ", inputstring," to find ", resulttype," but REGEX did not find result")
                try:
                    print()
                    retval = "?"*self.FIELDLENGTHS[resulttype]

                    #print("DEBUG Split_string retval:",retval)
                    return retval
                    
                except:
                    print("-------------------  APPLICATION ERROR: --------------------------")
                    print("split_string : FIELDLENGTHS does not have field ",resulttype)
                    print("-------------------------------------------------------------------")
                    exit(-1)
            


    # CONVERTS FILE SUFFIX TO SHORT DATE
    def tstoshortdate(self, x):
        return x[0:4]+"-"+x[4:6]+"-"+x[6:8]

    def colorvnfname(self,x):
        raise NotImplementedError("Must override parent")

    # Transforms value to MB/GB string format
    def mem_show_as_gb(self, value, convert):
        try:
            if convert:
                retval = int(int(value)/1024)
            else:
                retval = int(value)
            returnval = "{:>6s}".format(str(retval)+" GB")
            return returnval
        except:
            return "??"
    
    def show_as_percentage(self,myvalue , len,multiplier=1):
#    def show_as_percentage(self,numerator, denominator, len):
            #value_num=int(numerator)
            #value_den=int(denominator)
            #myvalue= int(100*value_num/value_den)
            returnval = "{:>3s}".format(str(myvalue*multiplier)+"%")
            return returnval.rjust(len)

    # REMOVES DT_NIMS from AZ/hostaggs
    def shorten_hostaggs(self, x):
        try:
            value= x.replace("DT_NIMS_", "")
            return value[0]
        except:
            #print("shorten_hostaggs : ERROR : value passed x is {:s}, result of replace is {:s}".format(x,value))
            return "?"

    def shorten_az(self, x):
        try:
            value= x.replace("DT_NIMS_", "")
            return value
        except:
            print("shorten_az : ERROR : value passed x is {:s}, result of replace is {:s}".format(x,value))
            return "?"         

    def shortenAAP(self, x):
        Retval= x.replace("active","A").replace("standby","S")
        return Retval
    

    def payload_json_parser(self, message):
        TestDict={}
        IsJSON=False
        try:
            # Message is native JSON
            TestDict=json.loads(message)
            IsJSON=True
        except:
            #Message is not native JSON: try key=value extraction
            
            ItemsList=message.split(' ')
            #print("ItemsList:",ItemsList)
            for Item in ItemsList:
                kv_pair=Item.strip().split('=')
                if len(kv_pair)==2:
                    TestDict[kv_pair[0]]=kv_pair[1]
                    IsJSON=True
                kv_pair=Item.split(":")
                #print("kv_pair:",kv_pair)
                if len(kv_pair)==2:
                    TestDict[kv_pair[0]]=kv_pair[1]
                    IsJSON=True
            #print("TestDict:",TestDict)
            #except:
            #    print("ItemsList:",ItemsList)
            #    print("TestDict:",TestDict)
            #    TestDict={}
            #    IsJSON=False
        return IsJSON,TestDict

# ----------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------
    def message_parser(self,messagedict):
        #print("-------report_library.py:message_parser------------")
        LOCALDEBUG=0
        resultdict={}
        messagedict_withhighlights={}
        JSONParsed_Dict={}
        #print("DEBUG1:")
        #print(json.dumps(messagedict,indent=10))
        for myKey in [x for x in list(messagedict.keys()) if x not in ['parsed_values', 'data_with_highlights', 'json_parsed_values']]:
            if LOCALDEBUG:
                print("-------------------")
                print("DEBUG TIER 0 myKey:",myKey)
            try:
                PayloadToParse= messagedict[myKey].lower().strip()
            except:
                print("Message parser ERROR")
                print(type( messagedict[myKey]))
                print("messagedict.keys():",messagedict.keys())
                print("myKey:",myKey)
                print("messagedict[myKey]:",messagedict[myKey])
                exit(-1)

            ModifiedPayload=PayloadToParse  
            counter=0
            countermax=len(self.Colorset["ReverseList"])
            Legenda_of_Colors={}
            for MyRegexKey in self.myRegexDict["message_parser"].keys():
                #if LOCALDEBUG:
                #    print("DEBUG TIER 1: MyRegexKey:",MyRegexKey)
                #    print("DEBUG TIER 1 : self.myRegexDict['message_parser'].keys():",self.myRegexDict["message_parser"].keys())
                MyRegexListPerKey,MyUncompiledRegexListPerKey=self.get_regex(MyRegexKey,"message_parser" )

                for MyRegex in MyRegexListPerKey:
                    PerKeyRegexCounter=MyRegexListPerKey.index(MyRegex)
                    #ResultTemp_search=MyRegex.search(PayloadToParse, re.DOTALL)
                    MyUncompiledRegex=MyUncompiledRegexListPerKey[PerKeyRegexCounter]
                    ResultIterator=[OneSearch for OneSearch in MyRegex.finditer(PayloadToParse)]
                    for ResultTemp_search in ResultIterator:
                        #print(ResultTemp_search)
                        var_Search_Matchdict=ResultTemp_search.groupdict()
                        OutputKey="result"
                        if ResultTemp_search.groupdict()[OutputKey] != None:
                            MatchingResultsListForKey=[ResultTemp_search.groupdict()[OutputKey] ]
                            #print("Result:",Result)
                            if MyRegexKey not in resultdict.keys():
                                resultdict[MyRegexKey]=[]
                            #print("Key:",myKey," MatchingResultsListForKey:",MatchingResultsListForKey)
                            #print("MatchingResultsListForKey is len0):",len(MatchingResultsListForKey))
                            for ValueFound in MatchingResultsListForKey :
                                #print("ValueFound:",ValueFound)
                                #print("ValueFound is None:",ValueFound is None)
                                if ValueFound:
                                    if ValueFound is not None:
                                        if len(ValueFound)>0 :
                                            if ValueFound not in resultdict[MyRegexKey]:
                                                #print(x,"--",type(x))
                                                resultdict[MyRegexKey].append(ValueFound)
                            
                        #print("resultdict:",json.dumps(resultdict,indent=4))

                        ForeColor=self.Colorset["ReverseList"][counter]
                        ResetColor=self.RESET
                        ModifiedPayload = re.sub(MyUncompiledRegex,
                            lambda x :  ForeColor+x.group(0)+ResetColor,
                            #lambda x :  menu.Backg_Red_ForeG_White+x.group(0)+menu.Backg_Default,
                            ModifiedPayload)
                        Legenda_of_Colors[myKey]=ForeColor+MyRegexKey+myKey+ResetColor
                    messagedict_withhighlights[myKey]=ModifiedPayload


                    IsJSON,TestDict= self.payload_json_parser(PayloadToParse)
                    if IsJSON:
                        JSONParsed_Dict[myKey]=TestDict
                counter+=1
                counter %=countermax

        return resultdict,messagedict_withhighlights,JSONParsed_Dict,Legenda_of_Colors

 # ----------------------------------------------------------------------------------------------------------------
    def message_parser_OLD(self,messagedict):
        #print("-------report_library.py:message_parser------------")
        LOCALDEBUG=0
        resultdict={}
        messagedict_withhighlights={}
        JSONParsed_Dict={}
        for myKey in messagedict.keys():
            if LOCALDEBUG:
                print("-------------------")
                print("DEBUG TIER 0 myKey:",myKey)
            PayloadToParse= messagedict[myKey].lower().strip()
            ModifiedPayload=PayloadToParse  

            for MyRegexKey in self.myRegexDict["message_parser"].keys():
                if LOCALDEBUG:
                    print("DEBUG TIER 1: MyRegexKey:",MyRegexKey)
                MyRegex=self.get_regex(MyRegexKey,"message_parser")
                
                ResultTemp_search=MyRegex.search(PayloadToParse, re.DOTALL)
                ResultIterator=[OneSearch for OneSearch in MyRegex.finditer(PayloadToParse)]
                for ResultTemp_search in ResultIterator:
                #if ResultTemp_search:
                    MyUncompiledRegex=self.get_uncompiled_regex("message_parser",MyRegexKey)
                    ModifiedPayload = re.sub(MyUncompiledRegex,
                        lambda x :  menu.Backg_Red_ForeG_White+x.group(0)+menu.Backg_Default,
                        #lambda x :  menu.Backg_Red_ForeG_White+x.group(0).upper()+menu.Backg_Default,

                        ModifiedPayload)
                    messagedict_withhighlights[myKey]=ModifiedPayload
                    OutputKey="result"
                    if OutputKey in ResultTemp_search.groupdict().keys():
                        if LOCALDEBUG:
                            print("DEBUG TIER 2.0> ResultTemp.groupdict():",json.dumps(ResultTemp_search.groupdict(),indent=4))
                            print("DEBUG TIER 2.1> resultTemp:",ResultTemp_search,"<<<")
                            print("DEBUG TIER 2.2> Result.groups():",ResultTemp_search.groups())
                            print("DEBUG TIER 2.3> myKey:",myKey," MyRegexKey:",MyRegexKey)
                            print("DEBUG TIER 2.4> resultTemp.group[result]:",ResultTemp_search.group("result"))

                        
                        Result=[ResultTemp_search.groupdict()[OutputKey]]
                        if LOCALDEBUG:
                            print("DEBUG TIER 3.0> Result:",Result)
                    else:
                        Result=[]
                    if MyRegexKey not in resultdict.keys():
                        resultdict[MyRegexKey]=[]
                        
                    for ValueFound in Result :
                        if ValueFound :
                            if len(ValueFound)>0 and ValueFound not in resultdict[MyRegexKey]:
                                #print(x,"--",type(x))
                                resultdict[MyRegexKey].append(ValueFound)


                messagedict_withhighlights[myKey]=ModifiedPayload
                IsJSON,TestDict= self.payload_json_parser(PayloadToParse)
                if IsJSON:
                    JSONParsed_Dict[myKey]=TestDict
        
        return resultdict,messagedict_withhighlights,JSONParsed_Dict
   
    def calc_max_percentage(self,num1, den1, num2, den2):
        retval= int(100*max(float (num1) / float (den1) , float (num2)/ float (den2)))
        return retval



class dynamic_report(report):

    def __init__(self,customreportType,inputdictionary, pars):
        super().__init__(pars)
        #print("Self.Screenwidth:",self.ScreenWidth)
        self.ReportType=customreportType
        self.set_name(customreportType)
        self.Parameters_Configdata_Backup=self.Parameters_Configdata.copy()
        var_Dict= self.Parameters_Configdata["Reports_Keys"]
        MyCustomReportIndexes=inputdictionary.keys()
        #print("DEBUG dynamic_report")
        #print(json.dumps(inputdictionary, indent=4))

        # Case 1 {"0":{record0},"1":{record1}....}
        if "0" in inputdictionary.keys():
            MyCustomReportKeys=[]
            MyCustomReportFieldLengths={}
            for Record in inputdictionary.keys():
                RecordKeys=Record.keys()
                for RecordKey in RecordKeys:
                    if RecordKey not in MyCustomReportKeys: 
                        MyCustomReportKeys.append(RecordKey)
                        MyCustomReportFieldLengths[RecordKey]=0
                    MyFieldLen=len(inputdictionary[Record] [RecordKey])
                    if MyFieldLen>MyCustomReportFieldLengths[RecordKey]:
                        MyCustomReportFieldLengths[RecordKey]=MyFieldLen

            var_Dict[self.ReportType+self.KEYS_KEYNAME]=MyCustomReportKeys
            var_Dict[self.ReportType+self.SORTINGKEYS_KEYNAME]=[MyCustomReportKeys[0]]
            var_Dict[self.ReportType+self.MULTILINEKEYS_KEYNAME]={"0":MyCustomReportKeys}
            #print(json.dumps(var_Dict, indent=10))
        else:
        # Case 1 {"key1":"value1","key2":"value2"....}
            MyCustomReportKeys=[]
            MyCustomReportFieldLengths={}
            MyCustomReportFieldTypes={}   
            for RecordKey in inputdictionary.keys():
                if RecordKey not in MyCustomReportKeys: 
                    MyCustomReportKeys.append(RecordKey)
                    MyCustomReportFieldLengths[RecordKey]=0
                if type(inputdictionary[RecordKey])==list:
                    for ValueItem in inputdictionary[RecordKey]:
                        MyFieldLen=len(ValueItem)
                        if MyFieldLen>MyCustomReportFieldLengths[RecordKey]:
                            MyCustomReportFieldLengths[RecordKey]=MyFieldLen+2
                else:
                    MyFieldLen=len(inputdictionary[RecordKey])
                    if MyFieldLen>MyCustomReportFieldLengths[RecordKey]:
                        MyCustomReportFieldLengths[RecordKey]=MyFieldLen+2
                    MyCustomReportFieldTypes[RecordKey]=type(inputdictionary[RecordKey])
            #print(json.dumps(var_Dict, indent=10))
            #print("DEBUG dynamic report")
            #print("BEFORE:")
            #print(json.dumps(self.Parameters_Configdata, indent=10))

            var_Dict[self.ReportType+self.KEYS_KEYNAME]=MyCustomReportKeys
            if len (MyCustomReportKeys)>0:
                var_Dict[self.ReportType+self.SORTINGKEYS_KEYNAME]=[MyCustomReportKeys[0]]
            var_Dict[self.ReportType+self.MULTILINEKEYS_KEYNAME]={}
            MultiLineIndex=0
            LenPerLine=0
            PerLineKeysList=[]
            #print("DEBUG: MyCustomReportKeys:", MyCustomReportKeys)
            #print("DEBUG: MyCustomReportFieldLengths:", MyCustomReportFieldLengths)

            for NewKey in MyCustomReportKeys:
                LenPerLine+=MyCustomReportFieldLengths[NewKey]
                if LenPerLine<=self.ScreenWidth:
                    PerLineKeysList.append(NewKey)
                    #print("DEBUG: PerLineKeysList:",PerLineKeysList, " of len:", LenPerLine,"/",self.ScreenWidth)
                else:
                    #print("DEBUG: NewLine: printing var_Dict[self.ReportType+self.MULTILINEKEYS_KEYNAME]")
                    MultiLineIndex+=1
                    tempDict={str(MultiLineIndex):PerLineKeysList}
                    PerLineKeysList=[]
                    PerLineKeysList.append(NewKey)
                    LenPerLine=len(NewKey)
                
                var_Dict[self.ReportType+self.MULTILINEKEYS_KEYNAME][str(MultiLineIndex)]=PerLineKeysList
            #print(json.dumps(var_Dict[self.ReportType+self.MULTILINEKEYS_KEYNAME],indent=10))   
            #var_Dict[self.ReportType+self.MULTILINEKEYS_KEYNAME]={"0":MyCustomReportKeys}
            #print(json.dumps(self.Parameters_Configdata["FieldLenghts"],indent=4))
            for NewKey in MyCustomReportKeys:
                if NewKey not in self.Parameters_Configdata["FieldLenghts"].keys():
                    self.Parameters_Configdata["FieldLenghts"][NewKey]=MyCustomReportFieldLengths[NewKey]
                if NewKey not in self.Parameters_Configdata["FieldLists"].keys():
                    self.Parameters_Configdata["FieldLists"][NewKey]=MyCustomReportFieldLengths[NewKey]
                
            #print("AFTER:")
            #print(json.dumps(self.Parameters_Configdata, indent=10))
            self.addemptyrecord()
            for DictKey in inputdictionary.keys():
                self.UpdateLastRecordValueByKey(DictKey,inputdictionary[DictKey])
 
    def restore_configdata(self):
        #print("BEFORE")
        #print(json.dumps(self.Parameters_Configdata,indent=4))
        self.Parameters_Configdata=self.Parameters_Configdata_Backup.copy()
        #print("AFTER")
        #print(json.dumps(self.Parameters_Configdata,indent=4))

        
        

# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
#                           CLASS :     MENU
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
class menu:
 
        
    # -------------------------------------------------------------------------------------------------------------------------
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
    DarkRed="\033[31;1;4"

    Grey = '\033[90m'
    Black = '\033[90m'
    Backg_Yellow= '\033[1;42m'
    Backg_Green= '\033[1;42m'
    Backg_Default='\033[1;0m'
    Backg_Red_ForeG_White= '\033[40;7m'+White
    Backg_Red='\033[40;7m'
    BackgRedBlink='\033[41;5m'
    Default = '\033[99m'

    

    ColorsList2 =(Backg_Red+OKBLUE,Backg_Red+OKCYAN,OKGREEN,WARNING,FAIL,White,Yellow,Magenta,Grey)


    