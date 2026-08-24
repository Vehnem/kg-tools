FROM python:3.9

WORKDIR /app

RUN apt-get update && \
    apt-get install -y wget unzip git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install git+https://github.com/AI-team-UoA/pyJedAI.git

COPY wrapper/ /app/

COPY fixes/matching.py /tmp/matching.py
COPY fixes/utils.py /tmp/utils.py

RUN cp /tmp/matching.py \
    /usr/local/lib/python3.9/site-packages/pyjedai/matching.py

RUN cp /tmp/utils.py \
    /usr/local/lib/python3.9/site-packages/pyjedai/utils.py

WORKDIR /app