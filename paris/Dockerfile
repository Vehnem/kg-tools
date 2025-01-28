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

COPY paris/requirements.txt .

COPY paris/config.json .

COPY _tool-wrapper/app.py .

RUN pip3 install -r requirements.txt

RUN wget https://github.com/dig-team/PARIS/releases/download/v0.3/paris_0_3.jar

CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]
