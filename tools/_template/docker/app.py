from flask import Flask
import subprocess

app = Flask(__name__)

@app.route('/')
def hello_geek():
    p = subprocess.run(["bash","./bin/tool.sh"], capture_output=True, text=True)
#    p = subprocess.run(["ls","-l"], capture_output=True, text=True, shell=True)
    return p.stdout

if __name__ == "__main__":
    app.run(debug=True)
