## A. P. Levine, 10th December 2018, a.levine[at]ucl.ac.uk

import sys

d=open(sys.argv[1],"r")
n=[]
for i in d:
	#s=i.rstrip("\n").split(" ")
	s=i.rstrip("\n")
	if s[0:4]=="<th>":
		this=s.lstrip("<th>").rstrip("</th>")
		this=this.replace("<br>"," ")
		this=this.replace(",","|")
		n.append(this)
	if s=="<tr>":
		n=[]
	if s[0:4]=="<td>":
		this=s.lstrip("<td>").rstrip("</td>")
		this=this.replace("<br>"," ")
		this=this.replace(",","|")
		n.append(this)
	if s=="</tr>":
		print ",".join(n)
