# Simplest Way to run Agreement Maker
### Requirements
- kg-testdata cloned in home directory
- JRE > 1.6
### Installation Instruction

Download https://github.com/dig-team/PARIS/releases/download/v0.3/paris_0_3.jar
```
wget https://github.com/dig-team/PARIS/releases/download/v0.3/paris_0_3.jar
```
Copy kg-testdata/_snippets/paris/person11.nt 
and  
Copy kg-testdata/_snippets/paris/person12.nt
```
cp /home/kg-testdata/_snippets/paris/person11.nt .
cp /home/kg-testdata/_snippets/paris/person12.nt .
```

Create Folder output
```
mkdir -p output
```
Run paris with output folder as output
```
java -jar paris_0_3.jar person11.nt person12.nt output
```