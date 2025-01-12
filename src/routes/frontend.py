# pyxfluff 2024-2025

from .. import app
from src.database import db
from src.reporting.report import daily_report

from time import time
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

root = Path(__file__).parents[1]
# day = round(time() / 86400)
day = 0

@app.get("/")
def index(req: Request):
    global day

    if day != round(time() / 86400):
        day = round(time() / 86400)
        daily_report(db)

    return FileResponse(root / "frontend" / "index.html")

@app.get("/to/<path:path>")
def social_to(req: Request, path):
    match path:
        case "discord":
            return RedirectResponse("https://discord.gg/3Q8xkcBT3M")
        case "git":
            # TODO (pyxfluff): git, i'm not doing query params work without intellisense lmao
            pass


for mount in [
    ("/", StaticFiles(directory = root / "frontend")),
]:
    app.mount(*mount)
