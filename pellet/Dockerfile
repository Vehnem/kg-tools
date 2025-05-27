FROM openjdk:8-jdk

RUN apt-get update && apt-get install -y git maven

RUN git clone https://github.com/stardog-union/pellet.git /pellet

WORKDIR /pellet

RUN mvn clean install

RUN chmod +x cli/target/pelletcli/bin/pellet

ENTRYPOINT ["cli/target/pelletcli/bin/pellet"]

