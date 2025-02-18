download:
	mkdir -p bin/; \
	wget https://github.com/AgreementMakerLight/AML-Project/releases/download/v3.2/AML_v3.2.zip -P bin; \
	cd bin; \
	unzip AML_v3.2.zip;

test:
	mkdir -p target/; \
	java -jar bin/AML_v3.2/*.jar -a -s $$KG_TESTDATA/rdf/agreementmaker/source.rdf -t $$KG_TESTDATA/rdf/agreementmaker/target.rdf -o target/output.rdf

