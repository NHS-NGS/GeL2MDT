# GeL2MDT #

### Instructions to install GEL2MDT

These have been tested on a clean installation of Ubuntu 16.04.4 LTS

### 1) VEP


    git clone https://github.com/Ensembl/ensembl-vep.git

Follow the onscreen instructions and install the cache directories for the latest release of the hg19 and hg38 repositories. 

To see the options for repositories, you can navigate to [here](ftp://ftp.ensembl.org/pub/release-X/variation/VEP/) where X is the latest release number.

Locally we have used the homo_sapiens_merged_vep_X_Y.tar.gz cache sources but the homo_sapiens_vep_91_GRCh38.tar.gz will work as well. 

We recommended running the convert_cache.pl script on the downloaded cache to speed up VEP queries. For more information see [here](http://www.ensembl.org/info/docs/tools/vep/script/vep_cache.html#cache)

You will also need to download fasta files pertaining the the hg19 and hg38 caches you have downloaded. 

For more information about installing VEP, please see [here](http://www.ensembl.org/info/docs/tools/vep/script/vep_download.html)

### 2) Anaconda

We recommend running GEL2MDT in a conda environment. For instructions about using conda, please see [here](https://docs.anaconda.com/anaconda/install/)

You can set up a conda environment called gel2mdt using the commands: 
    
    conda create -n gel2mdt python=3.6
    
### 3) Clone the GEL2MDT repository:
    
    
    git clone XXX
    cd gel2mdt
    #To install requirements
    pip install -r requirements
        
### 3) Setup Storage Locations

Before configuring GEL2MDT, you will need to create directories for storing data. The directories you will need to create are:

- A directory for storing JSON files you download from the CIP-API
- A directory for storing genes which are downloaded from the genenames API
- A directory for storing PanelApp JSON files

We download all these files to ensure that we have a record of what we get from each of these APIs. 

### 4) Configuring GEL2MDT

GEL2MDT has a config file which can be found in gelweb/gel2mdt/config/config.txt

This is where you can customise the application to your requirements. 

Here are the options and what they pertain to:

    center: Text; Name of your center
    vep: Path to VEP executable
    hg19_cache: Path to hg19 VEP cache
    hg19_fasta_loc: Path to hg19 fasta files
    hg38_cache: Path to hg38 VEP cache
    hg38_fasta_loc: Path to hg38 fasta files
    labkey_server_request: Labkey server path, for example:  Genomics England Portal/West Midlands/MeRCURy/Rare Diseases/Core
    labkey_cancer_server_request: Labkey server path for cancer cases. Similar to the one above
    cip_api_storage: Folder for storing CIP API JSONs
    panelapp_storage: Folder for storing PanelAPP JSONs
    gene_storage: Folder for storing genenames results
    bypass_VEP: Boolean; For testing usage, whether or not to byPass VEP
    cip_as_id: Boolean; By default the app uses GeL participant ID as primary ID of a proband. This changes the ID to CIP ID
    all_case_filtering: Boolean; Whether you want the main page to show all results
    mergedVEP=Boolean; Whether to use merged VEP cache directory with Ensembl and Refseq Transcripts
    remoteVEP=Boolean; Use if you want to run VEP on another server. The following options all refer to this
    remote_ip=IP address of remote server
    remote_username=User name for remote server
    remote_password=Password for remote server
    remote_directory=Folder for writing and transferring VEP output
    

Once these have been edited, please save the file. 

### 5) Database Setup

GEL2MDT has been tested in MySQL and PostgreSQL. Whichever one of these you choose, create a database called gel2mdt_db.

    CREATE DATABASE gel2mdt_db;
    
Then in the settings file gelweb/gelweb/settings/base.py add the DATABASE settings. 

An example of these can be found [here](https://docs.djangoproject.com/en/2.0/ref/settings/#databases)

For Postgres, the following instructions can assist with the installation [Link](https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04)

### 6) CIP API Setup

In the file DAILY_UPDATE.sh, add the following lines:

    export cip_api_username='username'
    export cip_api_password='password'
    
### 7) Configuring MultipleCaseAdder (MCA)

The settings for MCA can be specified in run_batch_update.py

MCA is the class which controls which cases are downloaded. The options are MCA are listed below:

    sample_type: Choice; Can be either 'raredisease' or 'cancer'
    head: Optional Number; used for downloading the first number of cases from the CIPAPI 
    test_data: Boolean; Switches from polling the CIPAPI to use the JSONs found in the directory gel2mdt/tests/test_files
    skip_demographics: Boolean; Turns off labkey querys and inserts 'unknown' demographics into the database
    sample: Optional TextField; The GELID of the single case you want to add from the CIPAPI
    pullt3: Boolean; Whether you want to pull Tier3 Variants for cases. Note there can be hundreds of T3 variants per case. 
    
    
The DAILY_UPDATE.sh script is a wrapper for running run_batch_update.py

For example the command to pull all raredisease cases from the CIPAPI is: 
    
    mca = MultipleCaseAdder(sample_type='raredisease', skip_demographics=False)

To run this, please use the command:

    sh DAILY_UPDATE.sh

