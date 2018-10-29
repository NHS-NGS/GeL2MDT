# Base image
FROM python:3.6

# Maintainer
MAINTAINER Patrick Lombard<patrick.lombard@gosh.nhs.uk>

ENV http_proxy=http://10.101.112.70:8080
ENV https_proxy=http://10.101.112.70:8080

# Install prequisites (last four entries added by me - PD)
RUN apt-get update && apt-get -y install \
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
    vim \
    mysql-server \
    default-libmysqlclient-dev

# Install VEP Perl dependencies
RUN cpanm DBI

# Install VEP. Using version 92 as per Gel2MDT Readme.  AUTO prevents prompts and -n prevents attempts to update
# which otherwise cause an unattended install to fail.
WORKDIR /root
RUN git clone https://github.com/Ensembl/ensembl-vep.git
WORKDIR /root/ensembl-vep
RUN perl INSTALL.pl --VERSION 92 --AUTO a -n

# Install Gel2MDT
RUN mkdir /root/gel2mdt
COPY . /root/gel2mdt
WORKDIR /root/gel2mdt
# This is already installed with Anaconda and fails to 'downgrade'. Remove from requirements file?
RUN sed -i 's/certifi==/# certifi==/g' requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN pip install mysqlclient
RUN pip install flower
# RUN pip install pip install Werkzeug
