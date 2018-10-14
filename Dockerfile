# Base image
FROM continuumio/miniconda3:4.5.11

# Maintainer
MAINTAINER Philip Davidson<philip.davidson2@nhs.net>

# Variables from docker-compose
ARG LABKEY_USERNAME
ARG LABKEY_PASSWORD
ARG DJANGO_SUPERUSER
ARG DJANGO_EMAIL
ARG DJANGO_PASSWORD
ARG CPI_API_USERNAME
ARG CPI_API_PASSWORD

# Install prequisites (last four entries added by me - PD)
RUN apt-get update && apt-get -y install \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    cpanminus \
    build-essential \
    git \
    unzip \
    curl \
    python-pip \
    libpango1.0-0 \
    libcairo2 \
    zlib1g-dev \
    vim

# Install VEP Perl dependencies
RUN cpanm DBI

# Install VEP. Using version 92 as per Gel2MDT Readme.  AUTO prevents prompts and -n prevents attempts to update
# which otherwise cause an unattended install to fail.
WORKDIR /root
RUN git clone https://github.com/Ensembl/ensembl-vep.git
WORKDIR /root/ensembl-vep
RUN perl INSTALL.pl --VERSION 92 --AUTO a -l -n

# Create virtual env and set path (equivalent to 'activate')
WORKDIR /root
RUN conda create -n gel2mdt python=3.6
ENV PATH /opt/conda/envs/gel2mdt/bin:$PATH

# Install Gel2MDT
RUN mkdir /root/gel2mdt
COPY . /root/gel2mdt
WORKDIR /root/gel2mdt
# This is already installed with Anaconda and fails to 'downgrade'. Remove from requirements file?
RUN sed -i 's/certifi==/# certifi==/g' requirements.txt
RUN pip install -r requirements.txt
RUN pip install psycopg2-binary gunicorn

# Make cache directories
WORKDIR /root/gel2mdt_cache
RUN mkdir -p cip_api_storage panelapp_storage gene_storage

# Copy config file from docker folder to correct gel2mdt folders
WORKDIR /root/gel2mdt/Docker
RUN cp my_local_settings.py ../gelweb/gelweb/settings/local_settings.py && \
    cp my_config.txt ../gelweb/gel2mdt/config/config.txt

# Create .netrc file for Labkey access
RUN printf "machine gmc.genomicsengland.nhs.uk\nlogin $LABKEY_USERNAME\npassword $LABKEY_PASSWORD" > /root/.netrc

# Add CIP-API credentials to environmental variables
ENV cip_api_username=$CPI_API_USERNAME
ENV cip_api_password=$CPI_API_PASSWORD

# Adds the superuser account & password to the 'initial_script.sh' for creating the account
RUN sed -i "s/DJANGO_SUPERUSER/$DJANGO_SUPERUSER/g" initial_script.sh && \
    sed -i "s/DJANGO_PASSWORD/$DJANGO_PASSWORD/g" initial_script.sh && \
    sed -i "s/DJANGO_EMAIL/$DJANGO_EMAIL/g" initial_script.sh

