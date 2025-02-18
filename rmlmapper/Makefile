INSTALL_DIR := $(CURDIR)/bin
KG_TESTDATA ?= $(HOME)/kg-testdata

.PHONY: download test clean

all: download test

download:
	wget -P $(INSTALL_DIR) https://github.com/RMLio/rmlmapper-java/releases/download/v7.2.0/rmlmapper-7.2.0-r374-all.jar

test:
	java -jar $(INSTALL_DIR)/rmlmapper-7.2.0-r374-all.jar --mapping $(KG_TESTDATA)/_snippets/rmlmapper/artist-map.ttl

clean:
	rm -rf $(INSTALL_DIR)
