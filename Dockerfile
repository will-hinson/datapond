# pull official base image
FROM python:3.11.1-slim-bullseye

# set work directory
WORKDIR /usr/src/datapond

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# declare a default failure chance of 0%. this should be
# set in a range of 0 (0%) to 1 (100%)
ENV DATAPOND_FAILURE_CHANCE 0.0

# copy the entire project to the work directory
ADD . /usr/src/datapond/

# install dependencies in work directory
RUN apt-get update
RUN apt-get -y install gcc
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
