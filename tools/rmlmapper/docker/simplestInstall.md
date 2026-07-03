# Simplest Way to run rmlmapper
### Requirements
- Java > 17
- cloned kg-testdata

### Installation Instruction

Download
```
wget -P $(INSTALL_DIR) https://github.com/RMLio/rmlmapper-java/releases/download/v7.2.0/rmlmapper-7.2.0-r374-all.jar
```

$(KG_TESTDATA) is cloned kg-testdata repository

Run Tests
```
java -jar rmlmapper-7.2.0-r374-all.jar --mapping $(KG_TESTDATA)/_snippets/rmlmapper/artist-map.ttl
```