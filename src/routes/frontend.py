# pyxfluff 2024-2025

from .. import app, is_dev
from src.database import db

if not is_dev:
    from src.reporting.report import daily_report
else:
    def daily_report(db):
        print("[x] Request to spawn daily report ignored due to missing modules")

from time import time
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

root = Path(__file__).parents[1]
# day = round(time() / 86400)
day = 0

@app.get("/")
async def index(req: Request):
    global day

    if day != round(time() / 86400):
        day = round(time() / 86400)
        (is_dev) and print("Ignoring reporting request, this will go through on prod") or daily_report(db)

    return FileResponse(root / "frontend" / "index.html")


for mount in [
    ("/", StaticFiles(directory = root / "frontend")),
]:
    app.mount(*mount)
