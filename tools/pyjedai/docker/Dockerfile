FROM python:3.8

WORKDIR /app

RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/*

RUN pip install pyjedai

COPY /wrapper /app/

#FIX VectorBasedMatching
COPY /fixes/matching.py /tmp/matching.py
RUN cp /tmp/matching.py /usr/local/lib/python3.8/site-packages/pyjedai/matching.py

WORKDIR /app