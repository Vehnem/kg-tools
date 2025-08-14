FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/*

COPY /wrapper /app/

RUN pip install pyjedai

WORKDIR /app