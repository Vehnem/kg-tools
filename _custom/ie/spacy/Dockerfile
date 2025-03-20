from mambaorg/micromamba

RUN micromamba create -n env python=3.12 pip spacy jupyter -c conda-forge
RUN micromamba run -n env pip install fuzzywuzzy spacy-entity-linker

RUN micromamba run -n env python -m spacy download en_core_web_sm

ADD ie.py .

ENTRYPOINT ["micromamba", "run", "-n", "env", "python", "ie.py"]