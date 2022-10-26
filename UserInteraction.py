
import os, sys
import json
import termios


class UserInteraction():

    def __init__(self, keyconfigfile="keysequence.json"):
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
            with open(keyconfigfile,"r") as file1:
                self.MatchSequences=json.load(file1)
            #print(json.dumps(self.MatchSequence,indent=5))

        except:
            print("ERROR: cannot find file ", keyconfigfile, " in current ./")
            exit(-1)


    def show_menu(self, menuname):
        InputCharacterMap= self.MatchSequences["keysequences"][menuname]
        ListOfAllowedKeys=list(InputCharacterMap.keys())
        MenuString=''
        for Item in InputCharacterMap.keys():
            MyDict=InputCharacterMap[Item]
            if "string" in MyDict.keys():
                ValueString=eval(MyDict["string"])
                MenuItem=" [{:1s}] {:}   ".format(MyDict["name"],MyDict["title"].format(ValueString))
            else:
                MenuItem=" [{:1s}] {:}   ".format(MyDict["name"],MyDict["title"])

            MenuString+=MenuItem        
        Stringa=self.FOREANDBACKGROUND.format(255,4)+self.FULL_LINE.format(MenuString)+self.Backg_Default
        print(Stringa)

    def getchars(self, menuname, echo=False):
        import termios
        import sys, tty
        def _getch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
        
            #try:
            tty.setraw(fd)
            GoOn=True
            InputSequence=[]
            while GoOn:
                MatchingSequence=[]
                ch = sys.stdin.read(1)
                InputSequence.append(ord(ch))
                if echo:
                    sys.stdout.write(ch)
                
                Sequencelen=len(InputSequence)

                for Key, Val in self.MatchSequences["keysequences"][menuname].items():

                    for Item in Val:
        #                if InputSequence[0:Sequencelen]==Item[0:Sequencelen]:

                        if InputSequence[0:Sequencelen]==Item[0:Sequencelen]:
                            PartialMatch=True
                            FullMatch=False
                            #print("PARTIAL MATCH with {:}={:}".format(InputSequence[0:Sequencelen], Item[0:Sequencelen]))
                        if InputSequence==Item:
                            FullMatch=True
                            PartialMatch=False
                            MatchingSequence.append(Key)

                #print("\n BEFORE InputSequence:",InputSequence,"\tMatchingSequence:", MatchingSequence, " Partial:",PartialMatch, " Full:",FullMatch, " GoOn:",GoOn)
   
                if FullMatch:
                    GoOn=False
                    return MatchingSequence
                if PartialMatch:
                    GoOn=True
                else:
                    GoOn=True
                    InputSequence=[]
                    MatchingSequence=[]
                #print("\n AFTER InputSequence:",InputSequence,"\tMatchingSequence:", MatchingSequence, " Partial:",PartialMatch,  " Full:",FullMatch," GoOn:",GoOn)

                #return MatchingSequence

            #finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            return MatchingSequence

        return _getch()


def main(args):
    UI=UserInteraction()
    GoOn=True
    val=UI.getchars(True)

    for item in val:
        print("item:", item)
    exit(-1)
    while GoOn:
        retval=UI.intercept_key_sequence()
        print(retval)
        #if retval=="change direction":
        exit(-1)

if __name__ == '__main__':
    main(sys.argv)

