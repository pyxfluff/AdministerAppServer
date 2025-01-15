# pyxfluff 2024

from src import __version__, app

from fastapi.responses import JSONResponse, RedirectResponse

import re
import time
import platform 

from sys import version
from fastapi import Request, APIRouter

from src.database import db

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"

t = time.time()
router = APIRouter()

print("OK, Imported!")

@app.get("/.administer/server")
async def verify_administer_server():
    return JSONResponse({
        "status": "OK",
        "code": 200,
        "server": "AdministerAppServer",
        "uptime": time.time() - t,
        "engine": version,
        "system": sys_string,
        "app_server_api_version": __version__,
        "target_administer_version": "1.0",
        "known_apps": len(db.get_all(db.APPS)),
        "banner": db.get("administer_banner", db.APPS),
        "banner_color": "#fffff"
    }, status_code=200)

@app.get("/to/{path:path}")
def social_to(path: str):
    if path.startswith("discord"):
        return RedirectResponse("https://discord.gg/3Q8xkcBT3M")
    elif path.startswith("git"):
        return RedirectResponse(f"https://github.com/administer-org/{path.removeprefix("git/")}")
    elif path.startswith("discourse"):
        return RedirectResponse("https://devforum.roblox.com/t/administer-modern-modular-free-admin-system-12/3179989")
    elif path.startswith("roblox"):
        return RedirectResponse("https://create.roblox.com/store/asset/127698208806211/Administer")
    elif path.startswith("docs"):
        return RedirectResponse("https://docs.administer.notpyx.me")

    return {"error": "That path isn't a valid shortlink."}

@app.get("/logs/{logid}")
def get_log(logid: str):
    log = db.get(logid, db.LOGS)
    if log is None:
        return JSONResponse({"error": "This logfile does not exist."}, status_code=404)
    return log

@app.get("/api-test")
def test():
    return "OK"

@app.get("/versions")
def administer_versions(req: Request):
    # hardcoded for now :3
    return JSONResponse({
        "provided_information": {
            "branch": "STABLE",
            "version": "1.2.3",
            "outdated": True,
            "can_update_to": {"branch": "STABLE", "name": "2.0.0"},
            "featureset": {
                "apps": {
                    "can_download": True,
                    "can_install_new": False,
                    "can_access_marketplace": True,
                },
                
                "administer": {
                    "can_auto_update": True,
                    "can_report_version": True
                },

                "misc": {
                    "supports_ranks": ["v2"]
                }
            }
        },

        "versions": {
            "2.0.0": {
                "latest": True,
                "available_to": ["STABLE", "CANARY"],
                "distributed_via": ["git", "roblox", "pesde", "aos-us_central"],
                "released": time.time(),
                "hash": "7c8e62d",

                "logs": ["a", "b", "c"]
            },

            "2.1.0-7c8e62d":{
                "latest": False,
                "available_to": ["git"],
                "distributed_via": ["git"],
                "released": time.time(),
                "hash": "7c8e62d",

                "logs": ["This is a prerelease directly from Git, as such we have no information."]
            },
        }
    })
