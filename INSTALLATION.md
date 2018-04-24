# GeL2MDT #

### Instructions to install GEL2MDT

These have been tested on a clean installation of Ubuntu 16.04.4 LTS

### 1) VEP


Please go [here](https://github.com/Ensembl/ensembl-vep) to download and install VEP. Only versions 91 and 92 of VEP have been tested with GEL2MDT. 

When using the INSTALL.pl script, please download a homo_sapiens cache. The refseq versions of these caches are not supported. The merged cache is supported and recommended if users want to see refseq transcripts. 

To see the list of repositories to download, you can navigate to [here](ftp://ftp.ensembl.org/pub/release-X/variation/VEP/) where X is the latest release number.

We recommended running the convert_cache.pl script on the downloaded cache to speed up VEP queries. For more information see [here](http://www.ensembl.org/info/docs/tools/vep/script/vep_cache.html#cache)

You will also need to download fasta files pertaining the the hg19 and hg38 caches you have downloaded. 

For more information about installing VEP, please see [here](http://www.ensembl.org/info/docs/tools/vep/script/vep_download.html)

### 2) Anaconda/Miniconda

We recommend running GEL2MDT in a conda environment. For instructions about installing conda, please see [here](https://docs.anaconda.com/anaconda/install/)

Once you have conda installed, to can set up a conda environment called gel2mdt use the commands: 
    
    conda create -n gel2mdt python=3.6
    
To activate it, use the following:
    
    source activate gel2mdt
    
### 3) Clone the GEL2MDT repository:
    
    
    git clone XXX
    cd gel2mdt
    pip install -r requirements
        
### 3) Setup Storage Locations

Before configuring GEL2MDT, you will need to create directories for storing data. The directories you will need to create are:

- A directory for storing JSON files you download from the CIP-API
- A directory for storing genes which are downloaded from the genenames API
- A directory for storing PanelApp JSON files

We download all these files to ensure there is a record of what is obtained from these APIs. 

### 4) Configuring GEL2MDT

To configure GEL2MDT, please edit gelweb/gel2mdt/config/example_config.txt and rename it to gelweb/gel2mdt/config/config.txt

If contributing to the project, please do not commit your configuration files and instead edit the example_config.txt file. 

Here are the options and what they pertain to:

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
    mergedVEP=Boolean; Whether to use merged VEP cache directory with Ensembl and Refseq Transcripts
    remoteVEP=Boolean; Use if you want to run VEP on another server. The following options all refer to this
    remote_ip=IP address of remote server
    remote_username=User name for remote server
    remote_password=Password for remote server
    remote_directory=Folder for writing and transferring VEP output
    GMC=Either a list of GMC's if intending to give users set options for GMC or 'None' to leave it as CharField. 
    pull_T3=Boolean; This gives users the option to download T3 so only set to False if you are not pulling T3's routinely
    email_address: Contact email address for users to submib bug reports

Please do not use quotation marks in this file.

### 5) Database Setup and editing settings file

GEL2MDT has been tested in MySQL and PostgreSQL. Whichever one of these you choose, create a database called gel2mdt_db.

    CREATE DATABASE gel2mdt_db;
    
Then in the settings file gelweb/gelweb/settings/base.py add the DATABASE settings. 

An example of these can be found [here](https://docs.djangoproject.com/en/2.0/ref/settings/#databases)

In gelweb/gelweb/settings/base.py, please enter a SECRET_KEY which used for hashing the website and is a long string. More information can be found [here](https://docs.djangoproject.com/en/2.0/ref/settings/#std:setting-SECRET_KEY). An example would be:

    SECRET_KEY = 'igfaddys&qa-myx=8%$d$$u!&w472)v!@at@ysahs)+4sx%h95'

In gelweb/gelweb/settings/base.py, please enter an ALLOWED_HOSTS which is the IP address of the machine you are running GeL2MDT. An example would be:
    
    ALLOwED_HOSTS = ['127.0.0.1']

There are multiple tutorials online about setting up a database for django and we would ask you to refer to those at this stage. 

Once you have a database setup, django will creates the tables and database structure for you. Users will have to run the following commands within your virtual environment:
    
    cd gelweb/
    python manage.py makemigrations gel2mdt
    python manage.py migrate
    python manage.py createinitialrevisions
    
If your settings are correct, you should see output similar to what is printed below:
    
    Running migrations:
      Applying contenttypes.0001_initial... OK
      Applying auth.0001_initial... OK
      Applying admin.0001_initial... OK
      Applying admin.0002_logentry_remove_auto_add... OK
      Applying contenttypes.0002_remove_content_type_name... OK
      Applying auth.0002_alter_permission_name_max_length... OK
      Applying auth.0003_alter_user_email_max_length... OK
      Applying auth.0004_alter_user_username_opts... OK
      Applying auth.0005_alter_user_last_login_null... OK
      Applying auth.0006_require_contenttypes_0002... OK
      Applying auth.0007_alter_validators_add_error_messages... OK
      Applying auth.0008_alter_user_username_max_length... OK
      Applying auth.0009_alter_user_last_name_max_length... OK
      Applying easyaudit.0001_initial... OK
      Applying easyaudit.0002_auto_20170125_0759... OK
      Applying easyaudit.0003_auto_20170228_1505... OK
      Applying easyaudit.0004_auto_20170620_1354... OK
      Applying easyaudit.0005_auto_20170713_1155... OK
      Applying easyaudit.0006_auto_20171018_1242... OK
      Applying gel2mdt.0001_initial... OK
      Applying gel2mdt.0002_auto_20180406_0741... OK
      Applying gel2mdt.0003_interpretationreportfamilypanel_custom... OK
      Applying gel2mdt.0004_auto_20180406_0746... OK
      Applying gel2mdt.0005_auto_20180410_0859... OK
      Applying gel2mdt.0006_auto_20180410_1054... OK
      Applying gel2mdt.0007_auto_20180411_0817... OK
      Applying gel2mdt.0008_gelinterpretationreport_sample_id... OK
      Applying gel2mdt.0009_auto_20180417_1546... OK
      Applying sessions.0001_initial... OK


Please note these commands may need to be rerun when you update GeL2MDT to reflect the changes in the database. 

### 6) CIP API and Labkey Setup

It is not recommended to keep CIP API credentials in source code which is why they are set as environment variables.

They can be set using the commands:
    
    export cip_api_username='username'
    export cip_api_password='password'
    
As a convenience, you could also add these lines to the DAILY_UPDATE.sh file. 

For Labkey, create the following file at ~/.netrc

    machine gmc.genomicsengland.nhs.uk
    login <login email address>
    password <login password>

### 7) Configuring MultipleCaseAdder (MCA)

The settings for MCA can be specified in gelweb/run_batch_update.py

MCA is the class which controls which cases are downloaded. The options are MCA are listed below:

    sample_type: Choice; Can be either 'raredisease' or 'cancer'
    head: Optional Number; used for downloading the first number of cases from the CIPAPI 
    test_data: Boolean; Switches from polling the CIPAPI to use the JSONs found in the directory gel2mdt/tests/test_files
    skip_demographics: Boolean; Turns off labkey querys and inserts 'unknown' demographics into the database
    sample: Optional TextField; The GELID of the single case you want to add from the CIPAPI
    pullt3: Boolean; Whether you want to pull Tier3 Variants for cases. Note there can be hundreds of T3 variants per case. 
    

For example the command to pull all raredisease cases from the CIPAPI is: 
    
    mca = MultipleCaseAdder(sample_type='raredisease', skip_demographics=False)

If this command is successful, the following output should appear:

    Polling API for case 6234-1
    Polling API for case 6240-1
    Polling API for case 6248-1
    ... 
    
The DAILY_UPDATE.sh script is a wrapper for running run_batch_update.py which could be added to your cronjobs and run every day.

### 8) Running GeL2MDT website

To create a superuser, please run the following and follow the prompts:
    
      python manage.py createsuperuser
      
To view the GeL2MDT website locally please run the following command and enter your credentials:
    
      python manage.py runserver
      
To deploy the website a webserver such as Apache/Nginx, please look up documentation for those tools.   
