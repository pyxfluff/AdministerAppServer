# pyxfluff 2024

from .. import app

from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

root = Path(__file__).parent.parent

@app.get("/")
def index(req: Request):
    return FileResponse(root / "frontend" / "index.html")

for mount in [
    ("/", StaticFiles(directory = root / "frontend")),
]:
    app.mount(*mount)