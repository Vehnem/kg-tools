from blacksheep import Application
from blacksheep.server.responses import text
from blacksheep import Request, get
import subprocess

app = Application()

@get("/run-openie")
async def run_openie(request: Request):
    input = request.query.get("input", "")

    result = subprocess.run(['python3', 'stanford-openie/extract.py', input[0]], capture_output=True, text=True)
    return text(result.stdout)

