# Simplest Way to run Agreement Maker
### Requirements
- kg-testdata cloned in home directory
- Oracle Java 1.7, 1.8, 1.9 or OpenJDK 1.8 installed (not tested for other versions)

### Installation Instruction

Download and unzip https://github.com/AgreementMakerLight/AML-Project/releases/download/v3.2/AML_v3.2.zip
```
wget https://github.com/AgreementMakerLight/AML-Project/releases/download/v3.2/AML_v3.2.zip
unzip AML_v3.2.zip 
rm AML_v3.2.zip
cd AML_v3.2
```
Copy kg-testdata/_snippets/agreementmaker/source.rdf  
and  
Copy kg-testdata/_snippets/agreementmaker/target.rdf  
```
cp /home/kg-testdata/_snippets/agreementmaker/source.rdf .
cp /home/kg-testdata/_snippets/agreementmaker/target.rdf .
```
Run in automatic mode with output.rdf as output
```
java -jar AgreementMakerLight.jar -a -s source.rdf -t target.rdf -o output.rdf
```