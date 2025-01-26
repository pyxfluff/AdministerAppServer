# pyxfluff 2024-2025

from .. import is_dev, app
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
day = 0


@app.get("/")
async def index(req: Request):
    global day

    if day != round(time() / 86400):
        day = round(time() / 86400)
        (is_dev) and print(
            "Ignoring reporting request, this will go through on prod"
        ) or daily_report(db)

    return FileResponse(root / "frontend" / "index.html")


@app.get("/app/{app:str}")
def app_frontend(req: Request, app: str):
    pass


@app.get("/to/{path:path}")
def social_to(path: str):
    if path.startswith("discord"):
        return RedirectResponse("https://discord.gg/3Q8xkcBT3M")
    elif path.startswith("git"):
        return RedirectResponse(
            f"https://github.com/administer-org/{path.removeprefix("git/")}"
        )
    elif path.startswith("discourse"):
        return RedirectResponse(
            "https://devforum.roblox.com/t/administer-modern-modular-free-admin-system-12/3179989"
        )
    elif path.startswith("roblox"):
        return RedirectResponse(
            "https://create.roblox.com/store/asset/127698208806211/Administer"
        )
    elif path.startswith("docs"):
        return RedirectResponse("https://docs.administer.notpyx.me")

    return {"error": "That path isn't a valid shortlink."}


for mount in [
    ("/", StaticFiles(directory=root / "frontend")),
]:
    app.mount(*mount)
