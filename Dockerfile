# Base image
FROM continuumio/miniconda3:4.5.11

# Maintainer
MAINTAINER Philip Davidson<philip.davidson2@nhs.net>

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
RUN perl INSTALL.pl --VERSION 92 --AUTO a -n

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

