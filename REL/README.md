For EL, the spans field needs to be set to an empty list. 
For ED, however, the spans field should consist of a list of tuples, where each tuple refers to the start position and length of a mention.

Example EL Request:

```bash
curl -X POST "https://rel.cs.ru.nl/api" -H "Content-Type: application/json" -d '{
    "text": "If you'\''re going to try, go all the way - Charles Bukowski",
    "spans": []
}'
```

Example ED Request:
```
curl -X POST "https://rel.cs.ru.nl/api" -H "Content-Type: application/json" -d '{
    "text": "If you'\''re going to try, go all the way - Charles Bukowski",
    "spans": [[41, 16]]
}'
```
