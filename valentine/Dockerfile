FROM python:3.11.2

WORKDIR /app

RUN pip3 install valentine

COPY wrapper/valentine_example.py .
COPY wrapper/valentine.sh .

COPY wrapper/valentine_example_v2.py .
COPY wrapper/valentine_v2.sh .
