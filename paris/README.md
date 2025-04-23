# Paris Quickstart

Requires

Settings at

Can not read other than files 

```
endIteration=3
factstore1=/home/marvin/papers/kg-testdata/bench1/samples/dbpedia_Person.100.nt
factstore2=/home/marvin/papers/kg-testdata/bench1/samples/wikidata_Person.100.nt
resultTSV=results
home = results

```

Issue when executing java -jar paris.jar path/to/file path/to/file out
when file1 and file2 are given as paths



Example Request:




```bash
curl -X POST \
  -F "flag=shared" \
  -F "file=@restaurant1.nt" -F "file_flag=" \
  -F "file=@restaurant2.nt" -F "file_flag=" \
  http://localhost:port/run
```
