# Simplest Way to run Valentine
### Requirements
- kg-testdata cloned in home directory
- Python >=3.9,<3.14
- Java
### Installation Instruction

Install Valentine
```
pip3 install valentine
```

Copy kg-testdata/_snippets/valentine/authors1.csv 
and  
Copy kg-testdata/_snippets/valentine/authors2.csv
```
cp /home/kg-testdata/_snippets/valentine/authors1.csv.
cp /home/kg-testdata/_snippets/valentine/authors2.csv .
```

Run 
```
python valentine_example.py authors1.csv authors1.csv
```