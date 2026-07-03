FROM python:3.10-slim

WORKDIR /app

ADD main.py .


RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/dig-team/FLORA.git
RUN cp main.py FLORA/src/
RUN cd FLORA && pip install -r requirements.txt

ADD wrapper/flora.sh .
