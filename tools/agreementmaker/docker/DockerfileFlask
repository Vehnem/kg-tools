FROM alpine:3.7

### Get Java via the package manager
RUN apk update \
&& apk upgrade \
&& apk add --no-cache bash \
&& apk add --no-cache --virtual=build-dependencies unzip \
&& apk add --no-cache curl \
&& apk add --no-cache openjdk8-jre

### Get Python, PIP
RUN apk add --no-cache python3 \
&& python3 -m ensurepip \
&& pip3 install --upgrade pip setuptools \
&& rm -r /usr/lib/python*/ensurepip && \
if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
rm -r /root/.cache

WORKDIR /app

RUN wget https://github.com/AgreementMakerLight/AML-Project/releases/download/v3.2/AML_v3.2.zip
RUN unzip AML_v3.2.zip && rm AML_v3.2.zip

WORKDIR /app/AML_v3.2

COPY agreementmaker/requirements.txt /app/AML_v3.2

COPY agreementmaker/config.json /app/AML_v3.2

COPY agreementmaker/example /app/AML_v3.2

COPY _tool-wrapper/app.py /app/AML_v3.2

RUN pip3 install -r requirements.txt

CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]
