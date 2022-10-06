import sys,os
import json
import string
import getch
import math


class TerminalMenu():

    def __init__(self, KeysFilename="keysequence.json"):
        self.screenrows, self.screencolumns = os.popen('stty size', 'r').read().split()
        self.ScreenWitdh = int(self.screencolumns)
        self.ScreenHeight = int(self. screenrows)   
        self.FULL_LINE="{0: ^"+str(self.ScreenWitdh)+"}"
        self.FOREANDBACKGROUND='\033[38;5;{:d};48;5;{:d}m'
        self.CLEARSCREEN ='\33[2J'
        self.RESETCOLOR='\033[0m'
        self.DEBUG=False
        self.total_result=[]
        try:
            with open(KeysFilename,"r") as file1:
                self.MatchSequence=json.load(file1)
            #print(json.dumps(self.MatchSequence,indent=5))
        except:
            print("ERROR: cannot find file ", KeysFilename, " in current ./")
            exit(-1)

    def get_all_keysequences(self):
        returnList=[]
        for Key,Value in self.MatchSequence["keysequences"].items():
            returnList+=Value
        return returnList
    
    def get_matchingsequence(self, listofinputchars):
        listofasciicodes=[]
        for x in listofinputchars:
            listofasciicodes.append(ord(x))
        if self.DEBUG:
            print("get_matchingsequence:listofasciicodes=",listofasciicodes)
        for Key,Value in self.MatchSequence["keysequences"].items():
            if self.DEBUG:
                print("checking full match")
            if listofasciicodes in Value:
                return Key, self.MatchSequence["sequence_delta"][Key]
            if self.DEBUG:
                print("checking partial match")
            partialmatch=False
            listofinputchars_len=len(listofinputchars)
            for IndividualKey in Value:
                shortened_list=IndividualKey[:listofinputchars_len]
                if self.DEBUG:
                    print("\t partial match : shortened_list=",shortened_list)
                if listofasciicodes== shortened_list:
                    return True, None

        if self.DEBUG:
            print("get_matchingsequence : did not find match for {:}".format(listofinputchars))
        return None, None

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

# ------------------- GET_KEY() -----------------
    def get_keymatch(self):
        HIGHERCONTINUE=True
        CONTINUE=True
        MATCHCHARS=[]
        while CONTINUE:
            OneChar=getch.getche()
            MATCHCHARS.append(OneChar)
            retval, retaction= self.get_matchingsequence(MATCHCHARS)
            if self.DEBUG:
                print("MATCHCHARS:",MATCHCHARS,"   RETVAL:",retval)
            if retval is None:
                MATCHCHARS=[]
                if self.DEBUG:
                    print("CLEARED MATCHARS:",MATCHCHARS)
            elif retval==True:
                if self.DEBUG:
                    print("partial Match")
            else:
                if self.DEBUG:
                    print("RETVAL:",retval)
                CONTINUE=False
        return retval, retaction

    def grab_children(self,father,nextdepth, depth_stack, total_list, local_list):
        print("--------------------------------NEW ---------")
        print("depth_stack at beginning:", depth_stack)
        print("nextdepth:",nextdepth)
        local_list=[]
        depth_stack.append(nextdepth)
        currentdepth=nextdepth
        
        if isinstance(father,dict):
            for key, value in father.items():
                local_list.append(key)
                nextdepth+=1
                print("---grab_children processing DICTIONARY: CURRENT DEPTH=",currentdepth, " NEXT RUN DEPTH:",nextdepth)
                print("---grab_children processing DICTIONARY: father keys=",father.keys())         
                temp_result, clear_depthstack= self.grab_children(value,nextdepth,depth_stack, total_list, local_list )
                local_list.extend(temp_result)
            return local_list, False
        elif isinstance(father, str):
            print("\tFINAL grab_children - processing STRING : for value:",father," with CURRENT DEPTH=",currentdepth, " NEXT RUN DEPTH:",nextdepth)
            local_list.append(father)
            depth_stack=[]
            return local_list, True

    def scan_dict(self,dictionary, result, totalresult,depthstack, id):
        id+=1
        print("----------------------------------------------------")
        print("STARTING ID:",id, "current unmodified RESULT:", result)
        if isinstance(dictionary, dict):
            for key, value in dictionary.items():
                print("\tDICTIONARY --------------------------------------------")
                print("\tID:", id, "DICTIONARY: scanning key:",key , " value=", value, "\n in dict : ***")
                if isinstance(value,dict):
                    result.append(key)
                else:
                    result.append(str(key)+'='+str(value))
                depthstack.append(id)
                retval = self.scan_dict(dictionary[key], result, totalresult,depthstack, id)
                print("\tID:", id, "DICTIONARY:  depth:", depthstack, " result:", result, "\n retval=",retval)
            if retval is not None:
                return retval
        elif isinstance(dictionary, list):
            print("\n\nLIST ? ? ? \n\n")
            exit(-1)
        elif isinstance(dictionary, str) or isinstance(dictionary, int):
            print("\tSTRING --------------------------------------------")
            #result.append(dictionary)
            self.total_result.append(result)
            result=[]
            print("\tID:", id, " depth:", depthstack, " result:", result)
            #print("\t self.total_result:",self.total_result)
            if dictionary is not None:
                return result
        else:
            print("Sounasega")
            exit(-1)


    def get_all_keys(self,dictionary, result):
        if isinstance(dictionary, dict):
            for key, value in dictionary.items():
                if isinstance(value,dict):
                    result.append(key)
                    retval = self.get_all_keys(dictionary[key], result)
                    if retval is not None:
                        return retval
        elif isinstance(dictionary, list):
            for item in dictionary:
                retval = self.get_all_keys(item, result)
                if retval is not None:
                    return retval

        elif isinstance(dictionary, str) or isinstance(dictionary, int):
            pass
        else:
            print("Sounasega")
            exit(-1)


            
    def indent_column(self,text, amount=5,  width=100, ch=' '):
        length=len(text)
        LinesOut=[]
        writablespace=width
        lines=math.ceil(length/writablespace)
        retval=""
        for count in range(lines):
            string_start= count*writablespace
            string_end = min((count+1)*writablespace,length-count*writablespace)
            #print("count:",count," string_start:",string_start," string_end:",string_end," length:",length, " writablespace:",writablespace)
            Line_string = amount*str(ch)+ text[string_start: string_end]
            #print("Line_string:",Line_string)
            LinesOut.append(Line_string)
            retval+=Line_string
            if count>0:
                retval+='\n'
        #print("Text:",text)
        #print("lines:",lines," length:",length," writable space:",writablespace)
        #print("retval:",retval)
        return retval, LinesOut


    def print_area(self, payload_dict, TopLeftRow, TopLeftCol, Width, Height,PointerRowCoord, PointerColCoord,countRow, countCol):
        stringa0="{:30s}"
        countCol+=1
        if isinstance(payload_dict,dict):
            for Key, Value in payload_dict.items():  
                if countRow==PointerRowCoord and countCol==PointerColCoord:
                    stringa = self.FOREANDBACKGROUND.format(0,255)+Key+self.RESETCOLOR              
                else:
                    stringa= self.FOREANDBACKGROUND.format(255,0)+Key+self.RESETCOLOR
                MyLine,MyRows = self.indent_column(stringa , TopLeftCol, Width)
                #if countLines<Height:
                print("{:}.{:}-".format(countRow,countCol)+MyLine)
                self.print_area(payload_dict[Key],TopLeftRow+10,TopLeftCol+10,160,160, PointerRowCoord, PointerColCoord, countRow, countCol)
                countRow+=1
            return MyLine, MyRows

        elif isinstance(payload_dict,str):
            stringa= self.FOREANDBACKGROUND.format(255,0)+payload_dict+self.RESETCOLOR
            MyLine,MyRows = self.indent_column(stringa , TopLeftCol+3, Width)
            if countRow<Height:
                print("{:}.{:}-".format(countRow,countCol)+MyLine)
            countRow+=1
            countCol=0
            return None,None




def querieslog_editor(args):
    mymenu= TerminalMenu()
    FILENAME="ELASTICSEARCH.QUERIES.LOG"
    with open(FILENAME,"r") as file1:
        QUERIESDICT= json.load(file1)
    InitialHighlightIndex=0
    Tier=0
    currentRow=0
    currentCol=0
    currentPos=[0]
    depth_stack=[]
    total_list=[]
    local_list=[]
    temp_dict={}
    depth=0
    id=0


    print(mymenu.get_all_keys(QUERIESDICT, total_list))
    print(total_list)
    exit(-1)
    #total_list= mymenu.grab_children(QUERIESDICT,depth, depth_stack, total_list, local_list)
    total_list= mymenu.scan_dict(QUERIESDICT,local_list,mymenu.total_result, depth_stack, depth )
    for item in mymenu.total_result:
        print(item)
    exit(-1)
    while True:
        os.system("clear")
        #for SkipLines in range (TopLeftRow):
        #    print()
        #stringa0= "{:"+str(Width)+"s}"
        mymenu.print_area(QUERIESDICT,0,0,mymenu.ScreenWitdh, mymenu.ScreenHeight,currentRow,currentCol,0,0)
        print(currentRow, "-",currentCol)
        intercepted_operation,intercepted_value = mymenu.get_keymatch()


        if intercepted_operation =="down":
            currentRow+=1
        elif intercepted_operation =="up":
            currentRow-=1
        elif  intercepted_operation =="right":
            currentCol+=1
        elif  intercepted_operation =="left":
            currentCol-=1
        else:
            pass
if __name__ == '__main__':
    querieslog_editor(sys.argv)
