# pyxfluff 2024

from src import __version__, app, accepted_versions, is_dev, default_app
from ..color_detection import get_color
from ..helpers import request_app

from fastapi import Request
from fastapi.responses import JSONResponse

import re
import time
import httpx
import platform

from io import BytesIO
from sys import version
from Levenshtein import ratio

from src.database import db
from src.models.RatingPayload import RatingPayload

import src

t = time.time()

blocked_users = db.get("__BLOCKED_USERS__", db.API_KEYS)
blocked_games = db.get("__BLOCKED__GAMES__", db.API_KEYS)
forbidden_ips = db.get("BLOCKED_IPS", db.ABUSE_LOGS) or []

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"

@app.get("/download-count")
async def download_stats():
    return JSONResponse({
        "schemaVersion": 1,
        "label": "Administer Downloads",
        "message": str(request_app(1)["AppDownloadCount"]),
        "color": "orange"  
    })

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
    
    place["ratings"][app_id] = {"rating": rating, "owned": True, "timestamp": time.time()}
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
            "start_ts": time.time(), # make it easier to catch abusers 
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

    db.set(app_id, app, db.APPS)
    db.set(req.headers.get("Roblox-Id"), place, db.PLACES)

    src.downloads_today += 1

    return JSONResponse({
            "code": 200,
            "message": "success",
            "user_facing_message": "Success!"
        }, status_code=200)

@app.get("/list")
async def app_list():
    apps = db.get_all(db.APPS)
    final = []
    _t = time.time()

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

    final.append({"processed_in": time.time() - _t})

    return JSONResponse(final, status_code=200)

@app.get("/rich-search/{search}")
async def search(req: Request, search: str):
    apps = db.get_all(db.APPS)
    final = []
    ratio_info = {"IsRatio": False}

    for app in apps:
        app = app["data"]
        del app["AppInstalls"]

        if search in app["AppTitle"]:
            app["IndexedBecause"] = "Name"
            final.append(app)

            continue
        elif ratio(search, app["AppName"]) >= .85:
            app["IndexedBecause"] = "NameRatio"
            ratio_info = {"IsRatio": True, "RatioKeyword": app["AppName"], "RatioConfidence": ratio(search, app["AppName"])}
            final.append(app)

            continue

        for tag in app["AppTags"]:
            if search in tag:
                app["IndexedBecause"] = "Tag"
                final.append(app)

                continue
            elif ratio(search, tag) >= .85:
                app["IndexedBecause"] = "NameRatio"
                ratio_info = {"IsRatio": True, "RatioKeyword": tag, "RatioConfidence": ratio(search, tag)}
                final.append(app)

                continue
    
    if final == []:
        return JSONResponse({
            "SearchIndex": "NoResultsFound",
            "RichSearchAPI": "2.0"
        }, status_code = 200)

    return JSONResponse({
        "SearchIndex": final,
        "RatioInfo": ratio_info,
        "RichSearchAPI": "2.0"
    }, status_code = 200)

@app.get("/misc-api/prominent-color")
async def get_prominent_color(image_url: str):
    if is_dev:
        return get_color(BytesIO(httpx.get(image_url).content))
    else: 
        # prevent vm IP leakage
        if not re.search(r'^https://tr\.rbxcdn\.com/.+', image_url):
            return JSONResponse({"code": 400, "message": "URL must be to Roblox's CDN."}, status_code=400)
        
        return get_color(BytesIO(httpx.get(image_url).content))

@app.get("/logs/{logid:str}")
def get_log(req: Request, logid: str):
    return db.get(logid, db.LOGS)

@app.post("/report-version")
async def report_version(req: Request):
    json = await req.json()
    key = db.get(round(time.time() / 86400), db.REPORTED_VERSIONS)
    branch = str(json["branch"]).lower()

    if not json["version"] in accepted_versions:
        return JSONResponse({"code": 400, "message": "Unsupported version, please update Administer."}, status_code=400)

    if not key:
        key = {
            "internal": {},
            "qa": {},
            "canary": {},
            "beta": {},
            "live": {},
        }

    if not key[branch].get(json["version"]):
        key[branch][json["version"]] = 0
    
    key[branch][json["version"]] += 1

    db.set(round(time.time() / 86400), key, db.REPORTED_VERSIONS)

    return JSONResponse({"code": 200, "data": {
        "EnableV2Nudge": False,
        "IsMarketplaceDisabled": False
    }}, status_code=200)

@app.post("/app-config/upload")
async def app_config(req: Request):
    config: {} = await req.json()
    id = config.get("Metadata", {}).get("AdministerID", len(db.get_all(db.APPS)))
    existing = db.get(id, db.APPS) or default_app
        

    print(config)
