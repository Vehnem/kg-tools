FROM alpine:3.19 AS builder

RUN apk add --no-cache curl unzip

WORKDIR /app
RUN curl -fsSL -o AML_v3.2.zip \
      https://github.com/AgreementMakerLight/AML-Project/releases/download/v3.2/AML_v3.2.zip \
 && unzip AML_v3.2.zip \
 && rm AML_v3.2.zip


FROM eclipse-temurin:8-jre-alpine

RUN apk add --no-cache bash coreutils

WORKDIR /app/AML_v3.2

COPY --from=builder /app/AML_v3.2/ ./
COPY wrapper/agreementmaker.sh .
RUN chmod +x agreementmaker.sh