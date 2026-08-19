FROM python:3.8

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install torch==1.9.0 torchtext==0.10.0 deepmatcher pyyaml

WORKDIR /app

ADD config-example.yaml .
ADD wrapper/run_deepmatcher.py .
ADD wrapper/deepmatcher.sh .
