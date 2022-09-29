import sys,os
import json
import string
from textwrap import indent
import simple_term_menu



def from_flatdict_to_nesteddict(flatdict):
    pass


def main(args):
    screenrows, screencolumns = os.popen('stty size', 'r').read().split()
    ScreenWitdh = int(screencolumns)
    Stringa0="{0: ^"+str(ScreenWitdh)+"}"
    FOREANDBACKGROUND='\033[38;5;{:d};48;5;{:d}m'
    RESETCOLOR='\033[0m'

    FILENAME="ELASTICSEARCH.QUERIES.LOG"
    with open(FILENAME,"r") as file1:
        QUERIESDICT= json.load(file1)

    print(json.dumps(QUERIESDICT,indent=4))
    TRANSFORMEDDICT={}
    for ExecutionTime in QUERIESDICT.keys():
        Notes=QUERIESDICT[ExecutionTime]["NOTES"].upper()
        CombinedFromToString= QUERIESDICT[ExecutionTime]["FROM"]+QUERIESDICT[ExecutionTime]["TO"]
        Endpoint= QUERIESDICT[ExecutionTime]["ENDPOINT"]

        if Notes not in TRANSFORMEDDICT.keys():
            TRANSFORMEDDICT[Notes]={}
        if CombinedFromToString not in TRANSFORMEDDICT[Notes].keys():
            TRANSFORMEDDICT[Notes][CombinedFromToString]={}
        if Endpoint not in TRANSFORMEDDICT[Notes][CombinedFromToString].keys():
            TRANSFORMEDDICT[Notes][CombinedFromToString][Endpoint]={}
        TRANSFORMEDDICT[Notes][CombinedFromToString][Endpoint][ExecutionTime]={}
        CMDLINE="python3 kibanaminer.py"
        for Item in QUERIESDICT[ExecutionTime].keys():
            if isinstance(QUERIESDICT[ExecutionTime][Item],str):
                CMDLINE+='--'+Item+' '+QUERIESDICT[ExecutionTime][Item]+' '
            elif  isinstance(QUERIESDICT[ExecutionTime][Item],list):
                CMDLINE+='--'+Item+' '+" ".join(QUERIESDICT[ExecutionTime][Item])+' '
            elif  isinstance(QUERIESDICT[ExecutionTime][Item],bool):
                if QUERIESDICT[ExecutionTime][Item]:
                    CMDLINE+='--'+Item+' '
        TRANSFORMEDDICT[Notes][CombinedFromToString][Endpoint][ExecutionTime]["CommandLine"]=CMDLINE
        TRANSFORMEDDICT[Notes][CombinedFromToString][Endpoint][ExecutionTime]["Record"]=QUERIESDICT[ExecutionTime]

        print(json.dumps(TRANSFORMEDDICT,indent=5))
        with open("ELASTICSEARCH.QUERIES.LOG.NEW","w") as file1:
            file1.write(json.dumps(TRANSFORMEDDICT, indent=4))

if __name__ == '__main__':
    main(sys.argv)
