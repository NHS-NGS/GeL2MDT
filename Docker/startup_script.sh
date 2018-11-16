#!/bin/bash
# This script runs on startup

# Create the netrc file for labkey login credentials
printf "machine gmc.genomicsengland.nhs.uk\nlogin $LABKEY_USERNAME\npassword $LABKEY_PASSWORD\n" > /root/.netrc

# Create the cache folders if they don't already exist
mkdir -p /root/gel2mdt_cache/cip_api_storage /root/gel2mdt_cache/panelapp_storage /root/gel2mdt_cache/gene_storage
