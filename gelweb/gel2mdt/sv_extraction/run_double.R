## A. P. Levine, 10th December 2018, a.levine[at]ucl.ac.uk

#Set path
e=read.csv("../Bone and Soft Tissue genetic alterations_APL_split.csv",colClasses="character")
unique.genes = unique(c(e[,1],e[,2]))
unique.genes=unique.genes[which(unique.genes!="")]
fusions=e[which(e$Gene2!=""),]
out=c()
for (i in 1:length(fusions[,1])){
	out=c(out,paste(sort(fusions[i,]),collapse="-"))
}
fusions.together=out

#Set path
v=read.table("../Version.txt",colClasses="character")
out=c()
for (i in 1:length(v[,1])){
	this1.s = strsplit(strsplit(v[i,1],"/")[[1]][2],":")[[1]]
	this2.s = strsplit(v[i,3],"]")[[1]]
	participant = strsplit(v[i,12],"]")[[1]][1]
	out=rbind(out,cbind(this1.s,this2.s,participant))
}
v2 = data.frame(out)
names(v2) = c("file","v","id")

output=c()
#Version 1.7, 1.8, v1.9
v178 = v2[which(v2[,2]!="v1.6"),1]
for (k in v178){
	p.id = as.character(v2$id[which(v2$file==k)])
	d=read.csv(paste(k,"Gene.csv",sep="_"),colClasses="character")
	two.genes = d[grep(" ", d$Gene),]
	if (length(two.genes[,1])>0){
		out=c()
		for (i in 1:length(two.genes[,1])){
			genes = sort(strsplit(two.genes[i,1]," ")[[1]])
			genes.together = paste(genes,collapse="-")
			out=rbind(out,cbind(genes[1],genes[2],genes.together))
		}
		out = data.frame(out)
		names(out) = c("Gene1","Gene2","Together")
		two.genes=cbind(two.genes,out)
	}
	found2 = two.genes[which(two.genes$Together %in% fusions.together),]
	if (length(found2[,1])>0){
		found2 = cbind(found2,"double")
		names(found2)[12] = "found"
		this.out=cbind(k,p.id,unique(as.character(found2$Together)))
		print(this.out)
		output=rbind(output,this.out)
	}
	if (length(found2[,1])==0){
		this.out=cbind(k,p.id,"None found")
		output=rbind(output,this.out)
	}
}

#Version 1.6
v16 = v2[which(v2[,2]=="v1.6"),1]
for (k in v16){
	p.id = as.character(v2$id[which(v2$file==k)])
	
	d=read.csv(paste(k,"SV.csv",sep="_"),colClasses="character")
	d$Gene1 = sapply(strsplit(d$Gene.Transcript.BP1," "),"[",1)
	d$Gene2 = sapply(strsplit(d$Gene.Transcript.BP2," "),"[",1)
	genes.together = c()
	for (i in 1:length(d[,1])){
		genes = sort(c(d$Gene1[i],d$Gene2[i]))
		genes.together = c(genes.together,paste(genes,collapse="-"))
	}
	d$Together= genes.together
	found2 = d[which(d$Together %in% fusions.together),]
	if (length(found2[,1])>0){
		found2 = cbind(found2,"double")
		names(found2)[12] = "found"
		this.out=cbind(k,p.id,unique(found2$Together))
		print(this.out)
		output=rbind(output,this.out)
	}
	if (length(found2[,1])==0){
		this.out=cbind(k,p.id,"None found")
		output=rbind(output,this.out)
	}
}

output = as.data.frame(output)
names(output) = c("Illumina","ID","Translocation")

write.csv(output,file="../translocations_found.csv",row.names=F,quote=F)