# syntax = docker/dockerfile:1.0-experimental
### NOTE: The comment line above is critical. It allows for the user of Docker Buildkit to inject secrets in the image at build time ###
# to build docker image
# $ export DOCKER_BUILDKIT=1
# $ docker build -t onedrive-offsite:latest .

FROM python:3.10.1-slim-bullseye


#### ---- ARGS AND ENVS FOR BUILD ---- ####

### - ENVS - ###

# default user
ENV USERNAME=onedriveoffsite
# set the python applications root directory
ENV PY_ROOT_DIR=/home/${USERNAME}/python_apps
# set the directory to store your python application
ENV PY_APP_DIR=${PY_ROOT_DIR}/onedrive-offsite
# set app etc dir for app json files
ENV ETC_DIR=/etc/onedrive-offsite
# set directory for working with large backup files
ENV BACKUP_FILES_DIR=/var/onedrive-offsite
# set the timezone info
ENV TZ=America/Chicago
# user that will send file
ENV FILE_USER=onedrivefile


#### ---- BASIC SYSTEM SETUP ---- ####

# check for updates 
# then upgrade the base packages
# set timezone
# Set the locale
# install tzdata package (to make timezone work)
# install nano
# disable root user
# create our default user (this user will run the app and api)
# create the file user with home directory (this user will send the backup files for upload via scp)
# make the .aws directory for py-basic-ses to read AWS SES credentials from
RUN  apt-get update && \
    apt-get upgrade -y && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get install locales -y && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen && \
    apt-get install tzdata -y && \
    apt-get install nano -y && \
    passwd -l root &&\
    $(useradd -s /bin/bash -m ${USERNAME}) &&\
    $(useradd -s /bin/bash -m ${FILE_USER}) && \
    mkdir /home/${USERNAME}/.aws

# setting local ENV variables
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8


#### ---- SSH ---- ####

# install openssh-server
# update sshd_config to only allow ssh via key pair
# create .keys directory
# adjust ownership of the .keys directory and its contents
RUN apt-get install openssh-server -y && \
    sed -i -e 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i -e 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && \
    sed -i -e 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config && \
	mkdir /home/${FILE_USER}/.keys && chown ${FILE_USER}:${FILE_USER} /home/${FILE_USER}/.keys && \	
    mkdir /home/${FILE_USER}/.ssh && chown ${FILE_USER}:${FILE_USER} /home/${FILE_USER}/.ssh && \	
    chmod -R 700 /home/${FILE_USER}/.keys && \
    chmod -R 700 /home/${FILE_USER}/.ssh


#### ---- PYTHON and APP ---- ####

# create directory for python app
# create etc directory
# make default user the owner of etc directory
# change etc directory permissions to be 700
# create backup files directory
# make default user the owner of backup files directory
# change backup files directory permissions to be 700
# create a directory to send the backup files to via scp and change permissions to 777 (need this to allow onedriveoffsite uesr to delete files)
# install pip3
# use pip to install gunicorn (for api)
RUN mkdir -p ${PY_APP_DIR} && \
    mkdir -p ${ETC_DIR} && \
    chown ${USERNAME}:${USERNAME} ${ETC_DIR} && \
    chmod 700 ${ETC_DIR} && \
    mkdir -p ${BACKUP_FILES_DIR} && \
    chown ${USERNAME}:${USERNAME} ${BACKUP_FILES_DIR} && \
    chmod 700 ${BACKUP_FILES_DIR} && \
    mkdir -p /home/${FILE_USER}/backup_files && chmod 777 /home/${FILE_USER}/backup_files && \
    apt-get install python3-pip -y && \
    pip install gunicorn

# copy the entire project into container image, so we can install it
COPY ./ ${PY_APP_DIR}/

# move into the root of the project directory
# install the project using the setup.py file and pip
# remove the entire project
RUN cd ${PY_APP_DIR} && \
    pip install . && \
    rm -R ./*

# copy in our entrypoint file (everything else should be installed)
COPY src/wsgi.py ${PY_APP_DIR}/



#### --- WHAT TO DO WHEN THE CONTAINER STARTS --- ####

#  restart the ssh server
#  change ownership recursively of python application directory so that USERNAME has privileges on files copied into image
#  make sure the default user owns the etc files
#  make sure the file transfer user owns their home directory
#  check for ssh key pair. if not present, create them.
#  move into the application directory
#  start the application with gunicorn
ENTRYPOINT service ssh restart && \
    chown -R ${USERNAME}:${USERNAME} ${PY_ROOT_DIR} && \
    chown -R ${USERNAME}:${USERNAME} ${ETC_DIR} && \
    chown -R ${FILE_USER}:${FILE_USER} /home/${FILE_USER} && \
    chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/.aws && \
    if [ -f /home/${FILE_USER}/.ssh/id_rsa ]; then echo "ssh keys exist, do not make new ones"; \
    else su ${FILE_USER} -c "ssh-keygen -t rsa -m SSH2 -f /home/${FILE_USER}/.ssh/id_rsa -q -N '' && \
    cat /home/${FILE_USER}/.ssh/id_rsa.pub > /home/${FILE_USER}/.ssh/authorized_keys" && echo "ssh keys created"; fi && \
    su ${USERNAME} -c "cd ${PY_APP_DIR} && \
    gunicorn --bind 0.0.0.0:8000 wsgi:api"
