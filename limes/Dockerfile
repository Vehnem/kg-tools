FROM openjdk:17-jdk-alpine

WORKDIR /app

RUN wget https://github.com/dice-group/LIMES/releases/download/1.8.3/limes.jar

CMD ["java", "-jar", "limes.jar", "-s", "-p", "5000"]
