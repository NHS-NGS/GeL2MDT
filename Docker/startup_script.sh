#!/bin/bash
# This script runs on startup

# User editable variables
CIP_API_USERNAME=phil.davidson
CIP_API_PASSWORD=mypassword
LABKEY_USERNAME=pdavidson
LABKEY_PASSWORD=mypassword

# Copy the two config files to the correct location in the django setup
cp /code/Docker/my_local_settings.py /root/gel2mdt/gelweb/gelweb/settings/local_settings.py
cp /code/Docker/my_config.txt /root/gel2mdt/gelweb/gel2mdt/config/config.txt

# Create the netrc file for labkey login credentials
printf "machine gmc.genomicsengland.nhs.uk\nlogin $LABKEY_USERNAME\npassword $LABKEY_PASSWORD\n" > /root/.netrc

# Create environmental variables for the CIP API login
export cip_api_username=$CIP_API_USERNAME
export cip_api_password=$CIP_API_PASSWORD

# Create the cache folders if they don't already exist
mkdir -p /root/gel2mdt_cache/cip_api_storage /root/gel2mdt_cache/panelapp_storage /root/gel2mdt_cache/gene_storage

