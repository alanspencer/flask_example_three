FROM python:3.7-slim

# Install enough packages to have SQL support

RUN apt-get update
RUN apt-get install -y  g++ gnupg2 curl

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

#Debian 10
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update
RUN echo msodbcsql17 msodbcsql/ACCEPT_EULA boolean true | debconf-set-selections
RUN yes | apt-get install msodbcsql17
RUN yes | apt-get install unixodbc-dev
# optional: kerberos library for debian-slim distributions
RUN apt-get install libgssapi-krb5-2

RUN pip install pyodbc

#Copy local files to Docker image

RUN mkdir -p /home/game
ADD static /home/game/static/
ADD templates /home/game/templates/
ADD *.py *.txt /home/game/
WORKDIR /home/game

RUN pip install -r requirements.txt
CMD flask run -h 0.0.0.0 -p 80
