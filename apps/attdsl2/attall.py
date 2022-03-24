#!/usr/bin/python3

import argparse
import attlanguage
import json
import sys

#
# setup the arguments parser
#


ap = argparse.ArgumentParser(description='Attest Elements Command Line Utility')
ap.add_argument('template', help="Location of the template file")
ap.add_argument('evaluation', help="Location of the evaluation file")
ap.add_argument('-r', '--restendpoint', help="Address of an A10REST endpoint", default="http://127.0.0.1:8520")
ap.add_argument('-P', '--prettyprint', help="Pretty print the report output",  action='store_true')
ap.add_argument('-p', '--progress', help="Show progress, 0=none, 1=a little,..., 5=lots",  type=int, default=0)
ap.add_argument('-o', '--outputfile', help="Write the output to the given file",  type=str)


args = ap.parse_args()

attf = None
evaf = None

with open(args.template,'r') as f:
    attf = f.read()

with open(args.evaluation,'r') as f:
    evaf = f.read()        

if (attf==None or evaf==None):
    print("Something went wrong with reading the att/eva files.")
    sys.exit(1)

ae = attlanguage.AttestationExecutor(attf,evaf,args.restendpoint)

if args.prettyprint==True:
    ae.prettyprint()

report = ae.execute(progress=args.progress)

print("of",args.outputfile)
if args.outputfile!=None:
    with open(args.outputfile,"w") as f:
        f.write(str(report.getReport()))

if args.prettyprint==True:
    pretty = json.dumps(report.getReport(), indent=4)
    print(pretty)

