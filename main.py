# darkpixlz 2024

from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from sys import version
from pathlib import Path
from types import FunctionType

import platform
import orjson as json
from models import RatingPayload

app = FastAPI()
app_server_version = "1.0"
roblox_lock = False

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: FunctionType) -> Response:
        print(request.headers.get("Roblox-id"))
        if roblox_lock and not request.headers.get("Roblox-id"):
            return JSONResponse({"code": 400, "message": "This App Server is only accepting requests from Roblox game servers."}, status_code=400)

        return await call_next(request)
    
app.add_middleware(AuthMiddleware)

def request_app(app_id):
    app_path = (Path("data/apps") / f"{app_id}.json")

    if not app_path.is_file():
        return None
    
    return json.loads(app_path.read_text())

@app.get("/.administer/server")
async def verify_administer_server():
    return JSONResponse({
        "code": 200,
        "server": "AdministerAppServer",
        "engine": version,
        "system": sys_string,
        "app_server_api_version": app_server_version,
        "target_administer_version": "1.0"
    }, status_code=200)

@app.get("/app/{appid}")
async def get_app(appid: str):
    try:
        app = request_app(appid)

        if app == None: raise FileNotFoundError
        return JSONResponse(app, status_code = 200)
    
    except (FileNotFoundError, OSError):
        return JSONResponse({
            "code": 404,
            "message": "not-found",
            "user_facing_message": "This app wasn't found. Maybe it was deleted while you were viewing it?"
        }, status_code=404)

@app.post("/rate/{app_id}")
async def rate_app(req: Request, app_id: str, payload: RatingPayload):
    place_file = (Path("data/places") / f"{req.headers.get("Roblox-Id")}.json")
    rating = payload.Rating
    
    if not place_file.is_file():
        return JSONResponse({
            "code": 400,
            "message": "bad-request",
            "user_facing_message": "Your place isn't in the database. Please try installing something and try again later."
        }, status_code=400)
    place_file = json.loads(place_file.read_text())

    if int(app_id) not in place_file["Installs"]:
        return JSONResponse({
            "code": 400,
            "message": "bad-request",
            "user_facing_message": "You have to install this app before you can rate it."
        }, status_code=400)

    app = request_app(app_id)
    if not app:
        return JSONResponse({
            "code": 404,
            "message": "not-found",
            "user_facing_message": "Could not find that app. Was it deleted?"
        }, status_code=404)
    
    if app_id in place_file["Ratings"]:
        place_file["Ratings"][app_id] = None
        app[rating and "AppLikes" or "AppDislikes"] -= 1
        print("Overwriting rating.")
    
    place_file["Ratings"][app_id] = {"Rating": rating, "DoesOwn": True}
    app[rating and "AppLikes" or "AppDislikes"] += 1

    (Path("data/apps") / f"{app_id}.json").write_bytes(json.dumps(app))
    (Path("data/places") / f"{req.headers.get("Roblox-Id")}.json").write_bytes(json.dumps(place_file))

    return JSONResponse({
            "code": 200,
            "message": "success",
            "user_facing_message": "Your review has been recoded, thanks for voting!"
        }, status_code=200)


@app.post("/install/{app_id}")
async def install_app(req: Request, app_id: str):
    place_file = (Path("data/places") / f"{req.headers.get("Roblox-Id")}.json")

    if not place_file.is_file():
        (Path("data/places") / f"{req.headers.get("Roblox-Id")}.json").write_bytes(json.dumps({"Installs": [],"Ratings":{}}))
        place_file = (Path("data/places") / f"{req.headers.get("Roblox-Id")}.json")

    place_file = json.loads(place_file.read_text())

    app = request_app(app_id)
    if not app:
        return JSONResponse({
            "code": 404,
            "message": "not-found",
            "user_facing_message": "Could not find that app. Was it deleted?"
        }, status_code=404)
    
    if app_id in place_file["Installs"]:
        return JSONResponse({
            "code": 400,
            "message": "bad-request",
            "user_facing_message": "This resource may only be used once."
        }, status_code=400)
    
    place_file["Installs"].append(app_id)
    app["AppDownloadCount"] += 1
    app["AppInstalls"].append(req.headers.get("Roblox-Id"))

    (Path("data/apps") / f"{app_id}.json").write_bytes(json.dumps(app))
    (Path("data/places") / f"{req.headers.get("Roblox-Id")}.json").write_bytes(json.dumps(place_file))

    return JSONResponse({
            "code": 200,
            "message": "success",
            "user_facing_message": "Success!"
        }, status_code=200)

@app.get("/list")
async def app_list():
    return JSONResponse((Path("data") / "list.json").read_text(), status_code=200)

@app.get("/query/{search}")
async def search():
    pass