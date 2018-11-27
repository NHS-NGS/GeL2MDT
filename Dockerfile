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
    default-libmysqlclient-dev \
    software-properties-common \
    screen

# RUN add-apt-repository ppa:webupd8team/java
RUN add-apt-repository "deb http://ppa.launchpad.net/webupd8team/java/ubuntu xenial main"
RUN echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections
RUN echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 seen true" | debconf-set-selections
RUN apt-get update
RUN apt-get install -y --allow-unauthenticated oracle-java8-installer maven \
    python3-dev python3-pip python3-virtualenv \
    libsasl2-dev libldap2-dev libssl-dev
RUN apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs
RUN apt-get install -y npm
RUN npm install avrodoc -g
# Install VEP Perl dependencies
RUN cpanm DBI

# Install VEP. Using version 92 as per Gel2MDT Readme.  AUTO prevents prompts and -n prevents attempts to update
# which otherwise cause an unattended install to fail.
WORKDIR /root
RUN git clone https://github.com/Ensembl/ensembl-vep.git
WORKDIR /root/ensembl-vep
RUN git checkout release/91
RUN perl INSTALL.pl --VERSION 91 --AUTO ap -n --PLUGINS all

# Install GelReportModels
RUN mkdir /gel
RUN mkdir /gel/GelReportModels
WORKDIR /gel
ADD GelReportModels /gel/GelReportModels
ADD GelReportModels/m2_settings.xml /gel
RUN mkdir -p ~/.m2 && cp m2_settings.xml ~/.m2/settings.xml
WORKDIR /gel/GelReportModels
RUN pip install --upgrade pip==18.0
ENV GEL_REPORT_MODELS_PYTHON_VERSION 3
RUN pip3 install .

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
