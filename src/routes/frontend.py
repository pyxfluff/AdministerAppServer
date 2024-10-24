# pyxfluff 2024

from .. import app
from src.database import db
from src.reporting.report import daily_report

from time import time
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

root = Path(__file__).parents[1]
day = round(time() / 86400)

@app.get("/")
def index(req: Request):
    if day != round(time() / 86400):
        day = round(time() / 86400)
        daily_report(db)

    return FileResponse(root / "frontend" / "index.html")

for mount in [
    ("/", StaticFiles(directory = root / "frontend")),
]:
    app.mount(*mount)