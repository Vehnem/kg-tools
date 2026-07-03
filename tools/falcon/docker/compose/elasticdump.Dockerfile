FROM node:18

# Installiere elasticdump
RUN npm install -g elasticdump

# Sicherstellen, dass elasticdump im PATH ist
ENV PATH="${PATH}:$(npm bin -g)"

ENTRYPOINT ["elasticdump"]

