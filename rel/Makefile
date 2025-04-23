VENV=.venv
INSTALL_DIR=bin
WIKI_VERSION=wiki_2019
BASE_URL=$(PWD)/$(INSTALL_DIR)
NAME_GENERIC=generic
URL_GENERIC=http://gem.cs.ru.nl/$(NAME_GENERIC).tar.gz
URL_WIKI=http://gem.cs.ru.nl/$(WIKI_VERSION).tar.gz

all: install setup test

install:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install radboud-el
	$(VENV)/bin/pip install gensim

setup:
	mkdir -p $(INSTALL_DIR)
	wget -O $(INSTALL_DIR)/$(NAME_GENERIC).tar.gz $(URL_GENERIC)
	tar -xzf $(INSTALL_DIR)/$(NAME_GENERIC).tar.gz -C $(INSTALL_DIR)
	rm $(INSTALL_DIR)/$(NAME_GENERIC).tar.gz
	wget -O $(INSTALL_DIR)/$(WIKI_VERSION).tar.gz $(URL_WIKI)
	tar -xzf $(INSTALL_DIR)/$(WIKI_VERSION).tar.gz -C $(INSTALL_DIR)
	rm $(INSTALL_DIR)/$(WIKI_VERSION).tar.gz

test:
	$(VENV)/bin/python3 test.py

clean:
	rm -rf $(VENV) $(INSTALL_DIR)

