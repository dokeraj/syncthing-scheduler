FROM python:alpine3.14

RUN pip install pyyaml
RUN pip3 install APScheduler
RUN pip3 install Flask
RUN pip3 install requests
RUN pip3 install six
RUN pip3 install waitress
RUN pip3 install wheel
RUN pip3 install environs
RUN pip3 install docker
RUN pip3 install macaddress


RUN mkdir /yaml
RUN mkdir /entry
RUN mkdir /sqldb

ADD configInit.py /entry/
ADD main.py /entry/
ADD sqliteDB.py /entry/
ADD statusController.py /entry/
ADD util.py /entry/

WORKDIR /entry/
CMD [ "python", "-u", "main.py" ]