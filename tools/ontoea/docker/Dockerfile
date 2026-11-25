FROM python:3.6.12

ARG ONTOEA_COMMIT=afa1c79281fdfca5b123fc8e6dfc8ceb41dd4ded

ENV ONTOEA_HOME=/app/OntoEA
ENV PYTHONPATH=/app/OntoEA/code/src
ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN git init OntoEA \
    && cd OntoEA \
    && git fetch --depth 1 https://github.com/ZihengZZH/OntoEA.git ${ONTOEA_COMMIT} \
    && git checkout FETCH_HEAD

WORKDIR /app/OntoEA
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir tqdm pyyaml \
    && pip uninstall -y smart_open \
    && pip install --no-cache-dir smart_open==5.2.1

WORKDIR /app/OntoEA/code/run
COPY wrapper/run_ontoea.py .
COPY wrapper/ontoea.sh .
COPY config-example.yaml .
COPY config-smoke.yaml .
RUN chmod +x ontoea.sh run_ontoea.py

ENTRYPOINT []
CMD ["bash", "ontoea.sh"]
