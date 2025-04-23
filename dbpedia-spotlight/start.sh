LANG=en
# Available languages: ca, da, de, en, es, fi, fr, hu, it, lt, nl, no, pt, ro, ru, sv, tr

# Create a volume to persist models
docker volume create spotlight-model

#Run docker image
docker run -tid \
 --restart unless-stopped \
 --name dbpedia-spotlight.$LANG \
 --mount source=spotlight-model,target=/opt/spotlight \
 -p 2222:80 \
 dbpedia/dbpedia-spotlight \
 spotlight.sh $LANG   
