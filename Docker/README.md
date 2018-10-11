# GeL2MDT Docker installation #

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

    The postgres database directory

    ```
    volumes:
        - <edit host directory>:/var/lib/postgresql/data 
    ```
    The directory containing the reference genomes (37 and 38) and .vep cache
    ```
    volumes:
        - <edit host directory>:/root/reference 
        - <edit host directory>:/root/vep_cache
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
The first time the images are build, Django needs to create the database schema, the commands for this are located in
the `initial_script.sh` script, so from the Docker directory, run (**for a one time creation of the database**):  

    run docker-compose run web bash initial_script.sh

Thereafter, you just need to run: 

    run docker-compose up

The system can be shutdown with:

    run docker-compose down

This destroys the containers and their associated network, but will leave the postgres databse on the host machine 
(assuming all has been configured correctly!)

### Caveats / To do...

- This runs the app using the Django development webservice - this needs to be rebuild with Nginx or Apache
- I have not configured the `DAILY_UPDATE.sh` script yet.
 
Contact:
philip.davidson2@nhs.net
