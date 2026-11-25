FROM maven:3.9-eclipse-temurin-17 AS build

ARG LOGMAP_COMMIT=a031fa9889e139fd5ab9e8c7415c8113f9c285ee

WORKDIR /build
ADD https://github.com/ernestojimenezruiz/logmap-matcher/archive/${LOGMAP_COMMIT}.tar.gz /tmp/logmap.tar.gz
RUN tar -xzf /tmp/logmap.tar.gz --strip-components=1 \
    && mvn -B -DskipTests package

FROM eclipse-temurin:17-jre

ENV LOGMAP_HOME=/opt/logmap

WORKDIR ${LOGMAP_HOME}
COPY --from=build /build/target/logmap-matcher-4.0.jar ${LOGMAP_HOME}/logmap-matcher.jar
COPY --from=build /build/target/java-dependencies ${LOGMAP_HOME}/java-dependencies
COPY --from=build /build/parameters.txt ${LOGMAP_HOME}/parameters.txt

WORKDIR /app
COPY wrapper/run_logmap.sh .
COPY config-example.conf .
RUN chmod +x run_logmap.sh

ENTRYPOINT []
CMD ["bash", "run_logmap.sh"]
