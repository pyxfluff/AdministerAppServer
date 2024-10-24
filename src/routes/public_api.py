# pyxfluff 2024

from src import __version__, app

from fastapi.responses import JSONResponse

import re
import time
import platform

from sys import version

from src.database import db

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"

t = time.time()

@app.get("/.administer/server")
async def verify_administer_server():
    return JSONResponse({
        "code": 200,
        "status": "OK",
        "uptime": time.time() - t,
        "server": "AdministerAppServer",
        "engine": version,
        "system": sys_string,
        "app_server_api_version": __version__,
        "target_administer_version": "1.0",
        "known_apps": len(db.get_all(db.APPS)),
        "banner": db.get("administer_banner", db.APPS),
        "banner_color": "#fffff"
    }, status_code=200)