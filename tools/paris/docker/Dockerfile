FROM alpine:3.19 AS builder

RUN apk add --no-cache curl

WORKDIR /app
RUN wget -O paris.jar https://github.com/dig-team/PARIS/releases/download/v0.3/paris_0_3.jar


FROM eclipse-temurin:8-jre-alpine

RUN apk add --no-cache bash

#&& apk add --no-cache --virtual=build-dependencies unzip \

WORKDIR /app

COPY --from=builder /app/paris.jar .

ADD wrapper/paris.sh .
ADD settings-example.ini .

RUN chmod +x paris.sh