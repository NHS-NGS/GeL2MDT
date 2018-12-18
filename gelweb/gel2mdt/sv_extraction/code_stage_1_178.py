## A. P. Levine, 10th December 2018, a.levine[at]ucl.ac.uk

import sys

check1="<h5>Non-redundant"
check2="<h5>Gene-centered"
if sys.argv[2]=="1":
	check=check1
if sys.argv[2]=="2":
	check=check2
start=0
start2=0
stop=0
d=open(sys.argv[1],"r")
for i in d:
	s=i.rstrip("\r\n").split(" ")
	n=[]
	for x in s:
		if x!="":
			n.append(x)
	if len(n)>0:
		if n[0]==check:
			start=1
		if start==1 and n[0]=="<table":
			start2=1
		if start==1 and start2==1 and n[0]=="</div>":
			stop=1
		if start==1 and start2==1 and stop==0:
			print " ".join(n)
