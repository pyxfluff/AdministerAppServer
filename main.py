# PyxFluff 2024

# Webserver API
from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Typing
from pathlib import Path
from types import FunctionType

# Prominent color detection
import socket, os
from colorthief import ColorThief
from urllib.request import urlretrieve

# Misc
import platform
import httpx
import orjson as json
from sys import version
from models import RatingPayload

app = FastAPI()
app_server_version = "1.0"
roblox_lock = False

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: FunctionType) -> Response:
        if roblox_lock and not request.headers.get("Roblox-id"):
            return JSONResponse({"code": 400, "message": "This App Server is only accepting requests from Roblox game servers."}, status_code=400)

        return await call_next(request)
    
app.add_middleware(AuthMiddleware)

def request_app(app_id):
    app_path = (Path("data/apps") / f"{app_id}.json")

    if not app_path.is_file():
        return None
    
    return json.loads(app_path.read_text())

@app.get("/")
async def root():
    return "OK"

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

@app.get("/misc-api/prominent-color")
async def get_prominent_color(image_url: str):
    path = socket.gethostname() == "codelet.obrien.lan" and "/Administer/tmp/Image.png" or ".Image.png"

    urlretrieve(image_url, path) # be friendly to windows devs who dont have ~
    color = ColorThief(path).get_color(quality=1)
    os.remove(path)    

    return color

@app.api_route("/proxy/{subdomain}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(subdomain: str, path: str, request: Request):
    target_url = f"https://{subdomain}.roblox.com/{path}"

    print(target_url)

    headers = dict(request.headers)
    headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    headers["host"] = f"{subdomain}.roblox.com"

    params = dict(request.query_params)

    async with httpx.AsyncClient() as client:
        if request.method == "GET":
            response = await client.get(target_url, headers=headers, params=params)
        elif request.method == "POST":
            form = await request.form()
            response = await client.post(target_url, headers=headers, params=params, data=form)
        elif request.method == "PUT":
            data = await request.body()
            response = await client.put(target_url, headers=headers, params=params, content=data)
        elif request.method == "DELETE":
            response = await client.delete(target_url, headers=headers, params=params)
        elif request.method == "PATCH":
            data = await request.body()
            response = await client.patch(target_url, headers=headers, params=params, content=data)
        elif request.method == "OPTIONS":
            response = await client.options(target_url, headers=headers, params=params)

    print(response.content)

    return response.content

