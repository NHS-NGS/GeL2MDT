# GeL2MDT Docker installation - experimental #

This docker configuration creates the following containers:
1. Nginx webserver
2. Gel2MDT Django installation which includes VEP and GeLReportModels
3. Postgres database backend
4. celery and celerybeat processes 
5. Flower for monitoring celery processes
5. Optional phpadmin for mysql installations


Whilst VEP is installed within the container, it requires that the reference genome files and VEP cache to be available 
on the host machine. These can be downloaded from the Ensembl ftp site. **As per the main Readme, Gel2MDT has been 
 tested with version 92 so that is the version that is installed. The correct VEP files will need to be downloaded to the host and be to reflect this.**

Likewise, in order to maintain a persistent database the Postgres/MySQL container stores the database files on the host 
machine, as are the cached JSON files from GEL.

### Clone the Repo
    git clone https://github.com/NHS-NGS/GeL2MDT.git
### Edit site-specific details
From the 'Docker' directory, edit the following files:


**example_credentials** 
Add your credentials to the example_credentials file and then move to /etc/gel2mdt folder. You may wish to put further 
restrictions on viewing/editing this file. 


**config file**
An example example config.txt file has included and may be edited and moved to gelweb/gel2mdt/config/. This 
can be edited as described in the main Readme.
- Edit the `labkey_server_request` and `labkey_cancer_server_request` URLs & `GMC` variables for your site
- _Leave_ all the VEP file locations and GeL2MDT file locations (these were edited in the docker-compose file)


**local_settings.py**
An example local_settings.py files has been included in this directory and may be moved to gelweb/gelweb/settings. This 
can be edited as described in the main Readme.
- Create your own `SECRET_KEY`
- Edit `ALLOWED_HOSTS` as appropriate
- Set `DEBUG` to `False` when you're done testing    
- _Leave_ the database connection settings unless you are also going to reconfigure the database docker container
- It is setup currently to update the database every night, please test this update process!


**docker-compose-prod.yml**:
Both types of supported databases have been included. Just uncomment the setup which is preferable. 
The following changes can be made:
- `Volumes` for the persistant postgres/mysql db on the host (db container), and reference fasta file and vep_cache 
(web container):

    Where the postgress/mysql db will reside on the host:

    ```
    db:
        volumes:
            - <edit host directory>:/var/lib/postgresql/data
    ```
    Where the vep cache and gel2mdt_cache (cip_api_storage, 
    panelapp_storage & gene_storage) directories, respectively, will reside on the host:
    ```
    web:
        volumes:
            - <edit host directory>:/root/.vep
            - <edit host directory>:/root/gel2mdt_cache
    ``` 

**Docker/initial_script.sh**
- Edit the main Django superuser credentials: `DJANGO_SUPERUSER`, `DJANGO_EMAIL` and `DJANGO_PASSWORD`

### Build the images
You can build the images with the standard:

    docker-compose -f docker-compose-prod.yml build
    
...however the first time a Django app is run, the app needs to create the database schema. So in order to keep this
 out of the build process (because you may need to build the container in a different location than it is being run) 
 _and_ out of the routine container startup, the commands for this are located in
the `initial_script.sh` script, so from the Docker directory, run (**for a one time creation of the database**):  

    docker-compose -f docker-compose-prod.yml run web bash /root/gel2mdt/Docker/initial_script.sh

Thereafter, you just need to run: 

    docker-compose -f docker-compose-prod.yml up

and system can be *stopped/started/removed with:

    docker-compose *stop/start/down

This `docker-compose down` will destroy the containers and their associated network, but will leave the persisent 
folders, i.e. postgres database on the host machine (assuming all has been configured correctly!)

### Gel2MDT will be available at http://<your_server>:8000
