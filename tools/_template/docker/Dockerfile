FROM python:3.12-alpine

WORKDIR app/

COPY . .
RUN pip3 install -r requirements.txt

CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]
