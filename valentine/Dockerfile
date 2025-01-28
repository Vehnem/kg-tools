FROM python:3.11.2

WORKDIR /app

COPY valentine/requirements.txt .

COPY valentine/config.json .

COPY valentine/valentine_example.py .

COPY valentine/data .

COPY _tool-wrapper/app.py .

RUN pip3 install -r requirements.txt

CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]
