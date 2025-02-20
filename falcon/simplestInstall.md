# Simplest Way to run Agreement Maker
### Requirements
- kg-testdata cloned in home directory
- pkg-config
- python ssl
- elasticdump
- elasticsearch

### Installation Instruction

Clone GitHub Repo
```
git clone https://github.com/SDM-TIB/falcon2.0.git
```

Replace all ElasticSearch Endpoints with local endpoint (es = Elasticsearch(['http://node1.research.tib.eu:9200/']) ->es = Elasticsearch(['http://localhost:9200/']))

Remove doc_type parameter from all es.search and es.index function calls

Install requirements
```
pip install -r requirements.txt
```

Download en_core_web_sm for spacy

```
python -m spacy download en_core_web_sm
```
Download ElasticSearch Dump and unzip

```
wget  https://figshare.com/ndownloader/files/20168714
unzip wikidata_dump.zip
rm wikidata_dump.zip
```

Start ElasticSearch
```
sudo systemctl start elasticsearch
```

Import Data to ElasticSearch (set Limit according to hardware specs)
```
elasticdump --output=http://localhost:9200/wikidataentityindex/ --input=wikidataentity.json --type=data --limit=10000
elasticdump --output=http://localhost:9200/wikidatapropertyindex/ --input=wikidataproperty.json --type=data --limit=10000
```

Run main.py
```
python main.py
```