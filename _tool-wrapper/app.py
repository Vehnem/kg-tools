from flask import Flask, request
import subprocess
import os
import json

app = Flask(__name__)

CONFIG_DIR = os.getcwd()

@app.route("/run", methods=["GET"])
def run_get():
    input = request.args.get('input', default='', type=str)
    flags = request.args.get('flags', default='', type=str)

    # Pfad zur Konfigurationsdatei für das Tool
    config_path = os.path.join(CONFIG_DIR, 'config.json')

    if not os.path.exists(config_path):
        return f"Error: No configuration found for tool '{CONFIG_DIR}", 404

    # Laden der Konfiguration für das Tool
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)

        # Befehl und Flags aus der Konfiguration lesen
        command = config.get("command")
        if not command:
            return f"Error: No command defined for tool '{CONFIG_DIR}'", 400

        # Füge zusätzliche Flags hinzu, wenn angegeben
        if flags:
            command.extend(flags.split())

        # Subprocess ausführen
        result = subprocess.run(command, input=input.encode('utf-8'),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')

    except Exception as e:
        return f"Error executing command for tool '{CONFIG_DIR}': {str(e)}", 500

@app.route("/run", methods=["POST"])
def run_post():
    # Überprüfen, ob Dateien im Request enthalten sind
    files = request.files.getlist('file')
    flags = request.form.getlist('flag')  # Allgemeine Flags (z.B. -p, -d)

    input = request.form.get('input')

    file_flags = request.form.getlist('file_flag')  # Datei-Flags (z.B. -f1, -f2)

    # Überprüfen, ob die Anzahl der Datei-Flags und Dateien übereinstimmt
    if len(files) != len(file_flags):
        return "The number of files and file_flags must match.", 400

    if not files:
        return "No files provided", 400

    # Pfad zur Konfigurationsdatei für das Tool
    config_path = os.path.join(CONFIG_DIR, 'config.json')

    if not os.path.exists(config_path):
        return f"Error: No configuration found for tool '{CONFIG_DIR}'", 404

    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)

        # Befehl aus der Konfiguration lesen
        command = config.get("command")
        if not command:
            return f"Error: No command defined for tool '{CONFIG_DIR}'", 400

        # Füge allgemeine Flags hinzu (z.B. -p 8000 -d)
        if flags:
            command.extend(flags)

        # Füge Datei-Flags und Dateien hinzu (z.B. -f1 file1 -f2 file2)
        for file, file_flag in zip(files, file_flags):
            # Temporär den Dateipfad speichern
            file_path = os.path.join(CONFIG_DIR, file.filename)
            file.save(file_path)

            # Flag und Datei zum Befehl hinzufügen (z.B. -f1 /path/to/file)
            if not file_flag:
                command.append(file_path)
            else:
                command.extend([file_flag, file_path])

        # Führe den Befehl aus
        result = subprocess.run(command, input=input.encode('utf-8'),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        # Wenn die Datei(en) am Ende nicht mehr gebraucht werden, lösche sie
        for file in files:
            os.remove(os.path.join(CONFIG_DIR, file.filename))

        return result.stdout.decode('utf-8')

    except Exception as e:
        return f"Error executing command for tool '{CONFIG_DIR}': {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

