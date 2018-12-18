## A. P. Levine, 10th December 2018, a.levine[at]ucl.ac.uk

#Extract version information from files (located in Supplementary directory)
grep Participant Supplementary/* | grep Version > Version.txt
#Find version 1.6 files
grep v1.6 Version.txt  | awk '{print $1}' | cut -d ":" -f 1 | cut -d "/" -f 2 > files_16.txt
#Find version 1.7, 1.8 and 1.9 files
grep -E "v1.7|v1.8|v1.9" Version.txt  | awk '{print $1}' | cut -d ":" -f 1 | cut -d "/" -f 2 > files_1789.txt


##For v1.6
for i in `cat files_16.txt`;
do echo $i
#Extract SVs
python code_stage_1_16.py Supplementary/${i} SV > analyse/${i}_SV
#Convert to CSV
python code_stage_2_simple.py analyse/${i}_SV  > analyse/${i}_SV.csv
rm analyse/${i}_SV
done

##For v1.7, v1.8, v1.9
for i in `cat files_1789.txt`;
do echo $i
#Extract gene-based
python code_stage_1_178.py Supplementary/${i} 2 > analyse/${i}_Gene
#Convert to CSV
python code_stage_2_simple.py analyse/${i}_Gene > analyse/${i}_Gene.csv
rm analyse/${i}_Gene
done

#Identify translocations involving both genes
Rscript run_double.R