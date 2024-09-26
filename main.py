# PyxFluff 2024

# Webserver API
from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Typing
from pathlib import Path
from types import FunctionType

# Prominent color detection
import socket, os
from random import randint
from colorthief import ColorThief
from urllib.request import urlretrieve

# Misc
import httpx
import platform

from time import time
import orjson as json
from sys import version
from collections import defaultdict

from modules.database import db
from modules.models import RatingPayload

t = time()
app = FastAPI()
app_server_version = "2.0"

api_lock = False
enable_sessions = False
roblox_lock = not "zen" in platform.release()

rate_limit_reqs = 25
rate_limit_reset = 120
rate_limit_max_incidents = 3

known_good_ips = []
limited_ips = defaultdict(list)
mem_incidents = defaultdict(list)
mem_blocked_ips = defaultdict(list)

blocked_users = db.get("__BLOCKED_USERS__", db.API_KEYS)
blocked_games = db.get("__BLOCKED__GAMES__", db.API_KEYS)
forbidden_ips = db.get("BLOCKED_IPS", db.ABUSE_LOGS) or []

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: FunctionType) -> Response:
        if request.headers.get("CF-Connecting-IP") in forbidden_ips:
            return JSONResponse({"code": 400, "message": "Sorry, but your IP has been blocked due to suspected abuse. Please reach out if this was a mistake."}, status_code=400)
        
        if roblox_lock:
            if request.url == "http://administer.notpyx.me/" or request.url == "http://administer.notpyx.me/":
                return await call_next(request) # allow the status bot to see the site
            
            if not request.headers.get("Roblox-Id") and not request.url == "http://administer.notpyx.me/":
                return JSONResponse({"code": 400, "message": "This App Server is only accepting requests from Roblox game servers."}, status_code=400)
            
            if request.headers.get("CF-Connecting-IP") in known_good_ips:
                # all is well
                return await call_next(request)
            
            elif "RobloxStudio" in request.headers.get("user-agent"):
                # Limit this on a per-API basis
                return await call_next(request)
            
            elif not httpx.get(f"http://ip-api.com/json/{request.headers.get("CF-Connecting-IP")}?fields=status,isp").json()["isp"] == "Roblox":
                db.set(request.headers.get("CF-Connecting-IP"), db.ABUSE_LOGS, {
                    "timestamp": time(), 
                    "ip-api_full_result":httpx.get(f"http://ip-api.com/json/{request.headers.get("CF-Connecting-IP")}?fields=status,message,country,regionName,isp,org,mobile,proxy,hosting,query").json(),
                    "roblox-id": request.headers.get("Roblox-Id"),
                    "user-agent": request.headers.get("user-agent", "unknown"),
                    "endpoint": request.url
                })

                forbidden_ips.append(request.headers.get("CF-Connecting-IP"))
                db.set("BLOCKED_IPS", forbidden_ips, db.ABUSE_LOGS)

                return JSONResponse({"code": 400, "message": "This App Server is only accepting requests from Roblox game servers. Possible API abuse detected, this incident will be reported."}, status_code=400)
            
            else:
                known_good_ips.append(request.headers.get("CF-Connecting-IP"))
            
        if api_lock and not request.headers.get("X-Administer-Key"):
            return JSONResponse({"code": 400, "message": "A valid API key must be used."}, status_code=400)
        
        elif api_lock and not db.get(request.headers.get("X-Administer-Key"), db.API_KEYS):
            return JSONResponse({"code": 400, "message": "This API key is not valid."}, status_code=400)
        
        elif api_lock:
            api_key_data = db.get(request.headers.get("X-Administer-Key"), db.API_KEYS)

            if api_key_data.disabled or api_key_data.registered_to in blocked_users or api_key_data.registered_game in blocked_games:
                return JSONResponse({"code": 400, "message": "Your API key has been disabled due to possible abuse. To reach out to the API team please join the discord and make a ticket (/discord)."}, status_code=400)
        
        if enable_sessions and not request.headers.get("X-Administer-Session"):
            return JSONResponse({"code": 400, "message": "A valid session token is required."}, status_code=400)

        return await call_next(request)
    
class RateLimiter(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: FunctionType) -> Response:
        cf_ip = request.headers.get("CF-Connecting-IP")

        if cf_ip in mem_blocked_ips:
            return Response(status_code=400, content="Sorry, you have been blocked. If you believe this is in error please reach out.")

        if not cf_ip:
            # development install?
            return await call_next(request)

        limited_ips[cf_ip] = [
            timestamp for timestamp in limited_ips[cf_ip]
            if timestamp > time() - rate_limit_reset
        ]

        if len(limited_ips[cf_ip]) >= rate_limit_reqs:
            return Response(status_code=429, content="Too many requests. Try again later. Do NOT refresh this page or else you will be blocked.")

        limited_ips[cf_ip].append(time())
        response = await call_next(request)
        return response
    
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimiter)

def request_app(app_id):
    return db.get(app_id, db.APPS)

@app.get("/")
async def root():
    return JSONResponse({
            "status": "OK",
            "code": 200,
            "uptime": time() - t,
            "app_server": app_server_version,
            "server_endpoint": "/.administer/server"
    }, status_code=200)

@app.get("/.administer/server")
async def verify_administer_server():
    return JSONResponse({
        "code": 200,
        "server": "AdministerAppServer",
        "engine": version,
        "system": sys_string,
        "app_server_api_version": app_server_version,
        "target_administer_version": "1.0",
        "known_apps": len(db.get_all(db.APPS)),
        "banner": db.get("administer_banner", db.APPS),
        "banner_color": "#fffff"
    }, status_code=200)

@app.get("/app/{appid:int}")
async def get_app(appid: int):
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
    if "RobloxStudio" in req.headers.get("user-agent"):
        return JSONResponse({
            "code": 400, 
            "message": "studio-restricted", 
            "user_facing_message": "Sorry, but this API endpoint may not be used in Roblox Studio. Please try it in a live game!"
        }, status_code = 400)
    
    place = db.get(req.headers.get("Roblox-Id"), db.PLACES)
    rating = payload.Rating
    
    if not place:
        return JSONResponse({
            "code": 400,
            "message": "bad-request",
            "user_facing_message": "We can't find your game."
        }, status_code=400)

    if app_id not in place["apps"]:
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
    
    if app_id in place["ratings"]:
        place["ratings"][app_id] = None
        app[rating and "AppLikes" or "AppDislikes"] -= 1
        print("Overwriting rating.")
    
    place["ratings"][app_id] = {"rating": rating, "owned": True, "timestamp": time()}
    app[rating and "AppLikes" or "AppDislikes"] += 1

    db.set(app_id, app, db.APPS)
    db.set(req.headers.get("Roblox-Id"), place, db.PLACES)

    return JSONResponse({
            "code": 200,
            "message": "success",
            "user_facing_message": "Your review has been recoded, thanks for voting!"
        }, status_code=200)


@app.post("/install/{app_id}")
async def install_app(req: Request, app_id: str):
    place = db.get(req.headers.get("Roblox-Id"), db.PLACES)

    if not place:
        place = {
            "apps": [],
            "ratings": {},
            "start_ts": time(), # make it easier to catch abusers 
            "start_source": ("RobloxStudio" in req.headers.get("user-agent") and "STUDIO" or "RobloxApp" in req.headers.get("user-agent") and "CLIENT" or "UNKNOWN")
        }

    app = request_app(app_id)
    if not app:
        return JSONResponse({
            "code": 404,
            "message": "not-found",
            "user_facing_message": "Could not find that app. Was it deleted?"
        }, status_code=404)
    
    if app_id in place["apps"]:
        return JSONResponse({
            "code": 400,
            "message": "bad-request",
            "user_facing_message": "This resource may only be used once."
        }, status_code=400)
    
    place["apps"].append(app_id)
    app["AppDownloadCount"] += 1
    app["AppInstalls"].append(req.headers.get("Roblox-Id"))

    db.set(app_id, app, db.APPS)
    db.set(req.headers.get("Roblox-Id"), place, db.PLACES)

    return JSONResponse({
            "code": 200,
            "message": "success",
            "user_facing_message": "Success!"
        }, status_code=200)

@app.get("/list")
async def app_list():
    apps = db.get_all(db.APPS)
    final = []
    _t = time()

    for app in apps:
        app = app["data"]

        final.append(
            {
                "AppName": app["AppName"],
                "AppShortDescription": app["AppShortDescription"],
                "AppDownloadCount": app["AppDownloadCount"],
                "AppRating": ((app["AppLikes"] + app["AppDislikes"]) == 0 and "---%" or app["AppLikes"] / (app["AppLikes"] + app["AppDislikes"])),
                "AppDeveloperID": app.get("AppDeveloperID", 0),
                "UpdatedAt": app["AppUpdatedUnix"],
                "AppID": app["AdministerMetadata"]["AdministerID"],
                "AppType": app["AppType"]
            }
        )

    final.append({"processed_in": time() - _t})

    return JSONResponse(final, status_code=200)

@app.get("/query/{search}")
async def search(req: Request, search: str):
    return db.raw_find_all({"AppName": search.lower()}, db.APPS)

@app.get("/misc-api/prominent-color")
async def get_prominent_color(image_url: str):
    # be friendly to windows devs who dont have ~
    path = f"{socket.gethostname() == "codelet.obrien.lan" and "/Administer/tmp/Image.png" or ".Image.png"}-r{randint(1, 2500)}"

    urlretrieve(image_url, path)
    color = ColorThief(path).get_color(quality=1)
    os.remove(path)    

    return color

@app.api_route("/proxy/{subdomain}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(subdomain: str, path: str, request: Request):
    target_url = f"https://{subdomain}.roblox.com/{path}"

    headers = dict(request.headers)
    headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    headers["host"] = f"{subdomain}.roblox.com"

    headers.pop("roblox-id", None)
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

    return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))

@app.get("/headers")
def headers(req: Request):
    return req.headers