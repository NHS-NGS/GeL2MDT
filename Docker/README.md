# GeL2MDT Docker installation - experimental #

This docker configuration creates two containers:
1. Gel2MDT Django installation with VEP
2. Postgres database backend

Whilst VEP is intalled within the container, it requires that the reference genome files and VEP cache to be available on the host machine.
Likewise, in order to maintain a persistent database the Postgres install stores the database files on the local machine and the cached JSON files from GEL are also stored on the host.

### Clone the Repo
    git clone -b docker https://github.com/KingsPM/GeL2MDT.git
### Edit site-specific details
From the 'Docker' directory, edit the following files where necessary (don't rename or move these files, they will be 
copied to the correct location during the image build):

**docker-compose.yml**:
- Edit the `CPI_API_USERNAME` and `LABKEY_USERNAME` and password fields with the credentials you will use to connect 
to relevant GEL services
- Edit the main Django superuser credentials: `DJANGO_SUPERUSER`, `DJANGO_EMAIL` and `DJANGO_PASSWORD`
- `Volumes` for the persistant postgres db on the host (db container), and reference fasta file and vep_cache 
(web container):

    Where the postgress db will reside on the host:

    ```
    db:
        volumes:
            - <edit host directory>:/var/lib/postgresql/data
    ```
    Where the reference genome fasta files, vep cache and gel2mdt_cache (cip_api_storage, 
    panelapp_storage & gene_storage) directories, respectively, will reside on the host:
    ```
    web:
        volumes:
            - <edit host directory>:/root/reference
            - <edit host directory>:/root/vep_cache
            - <edit host directory>:/root/gel2mdt_cache
    ``` 
**my_config.txt**:
- Edit the `labkey_server_request` and `labkey_cancer_server_request` URLs & `GMC` variables
- Leave all the VEP file locations and GeL2MDT file locations (these were edited in the docker-compose file)

**my_local_settings.py**:
- Create your own `SECRET_KEY`
- Edit `ALLOWED_HOSTS` as appropriate
- Set `DEBUG` to `False` when you're done testing    
- Leave the database connection settings unless you are also going to reconfigure the database docker container

### Build the images
You can build the images with the standard:

    docker-compose build
    
...however the first time a Django app is run, the app needs to create the database schema. So in order to keep this
 out of the build process _and_ out of the routine containter startup, the commands for this are located in
the `initial_script.sh` script, so from the Docker directory, run (**for a one time creation of the database**):  

    docker-compose run web bash initial_script.sh

Thereafter, you just need to run: 

    docker-compose up

and system can be *stopped/started/removed with:

    docker-compose *stop/start/down

This `docker-compose down` will destroy the containers and their associated network, but will leave the persisent 
folders, i.e. postgres database on the host machine (assuming all has been configured correctly!)

### Caveats / To do...

- This runs the app using the Django development webservice - this needs to be rebuild with Nginx or Apache
- I have not configured the `DAILY_UPDATE.sh` script yet
- Need to think about permissions for the host directories
 
Contact:
philip.davidson2@nhs.net
