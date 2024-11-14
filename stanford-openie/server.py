from dataclasses import dataclass
from blacksheep import Application, FromJSON, FromQuery, get, post, StreamedContent, Response, Request
# import asyncio

from blacksheep.server.openapi.v3 import OpenAPIHandler
from openapidocs.v3 import Info

app = Application()

docs = OpenAPIHandler(info=Info(title="Example API", version="0.0.1"))
docs.bind_app(app)

@dataclass
class CreateJedaiInput:
    file1: str
    file2: str

@post("/")
async def jedai(data: FromJSON[CreateJedaiInput]):
    jedaiInput = data.value
    return jedaiInput.file1

@post("/chunked-text")
async def get_chunked_text(request: Request):
    async def provider():
        async for chunk in request.stream():
            yield chunk

    return Response(200, content=StreamedContent(b"text/plain", provider))
