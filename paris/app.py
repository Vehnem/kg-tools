from flask import Flask, request
import subprocess

app = Flask(__name__)


@app.route("/run-fasttrack")
def run_fastrack():
    kb1 = request.args.get("kb1", "")
    kb2 = request.args.get("kb2", "")
    outputfolder = request.args.get("outputfolder", "")

    result = subprocess.run(['java', '-jar', 'paris_0_3.jar', kb1, kb2, outputfolder],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
    return result.stdout.decode('utf-8')


@app.route("/run-detailedtrack")
def run_detailedtrack():
    settingsfile = request.args.get("settingsfile", "")

    result = subprocess.run(['java', '-jar', 'paris_0_3.jar', settingsfile],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)

    return result.stdout.decode('utf-8')

if __name__ == "__main__":
    app.run(debug=True)

