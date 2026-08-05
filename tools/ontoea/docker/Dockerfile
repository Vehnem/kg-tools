FROM python:3.6.12

WORKDIR /app

RUN git clone https://github.com/ZihengZZH/OntoEA.git

RUN cd OntoEA && pip install -r requirements.txt && cd ..

RUN pip install tqdm

RUN pip uninstall smart_open -y && pip install smart_open==5.2.1

RUN export PYTHONPATH=/app/OntoEA/code/src

WORKDIR /app/OntoEA/code/run

COPY wrapper/ontoea.sh .