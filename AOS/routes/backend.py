# pyxfluff 2024 - 2025

from AOS import globals
from ..color_detection import get_color
from ..helpers import request_app

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

import re
import time
import httpx
import platform

from io import BytesIO
from sys import version
from Levenshtein import ratio

from AOS.database import db
from AOS.models.RatingPayload import RatingPayload

sys_string = f"{platform.system()} {platform.release()} ({platform.version()})"


class BackendAPI:
    def __init__(self, app):
        self.app = app
        self.startup_time = time.time()
        self.router = APIRouter()
        self.asset_router = APIRouter(prefix="/asset")

        self.blocked_users = db.get("__BLOCKED_USERS__", db.API_KEYS)
        self.blocked_games = db.get("__BLOCKED__GAMES__", db.API_KEYS)
        self.forbidden_ips = db.get("BLOCKED_IPS", db.ABUSE_LOGS) or []

    def initialize_api_routes(self):
        @self.router.get("/ping")
        async def ping():
            return "OK"
        
        @self.router.get("/get_download_count")
        async def download_stats():
            return JSONResponse(
                {
                    "schemaVersion": 1,
                    "label": "Administer Downloads",
                    "message": str(request_app(1)["downloads"]),
                    "color": "orange",
                }
            )

        @self.router.get("/directory")
        async def app_list(req: Request, asset_type: str):
            apps = db.get_all(db.APPS)
            final = []
            _t = time.time()

            for app in apps:
                app = app["data"]

                final.append(
                    {
                        "name": app["name"],
                        "short_desc": app["short_desc"],
                        "downloads": app["downloads"],
                        "AppRating": (
                            (app["votes"]["likes"] + app["votes"]["dislikes"]) == 0
                            and "--.--%"
                            or app["votes"]["likes"]
                            / (app["votes"]["likes"] + app["votes"]["Dislikes"])
                        ),
                        "developer": {
                            "id": app.get("AppDeveloperID", 0),
                        },
                        "last_update": app["AppUpdatedUnix"],
                        "id": app["administer_metadata"]["id"],
                        "object_type": app["type"],
                    }
                )

            if final == []:
                final = [
                    {
                        "object_type": "message",
                        "text": "This marketplace server does not have any objects with the requested type.",
                    }
                ]

            final.append({"processed_in": time.time() - _t})

            return JSONResponse(final, status_code=200)

        @self.router.get("/search/{search}")
        async def search(req: Request, search: str):
            apps = db.get_all(db.APPS)
            final = []
            ratio_info = {"is_ratio": False}

            if search in [None, "", " "]:
                return JSONResponse(
                    {"index": "invalid_query", "search_api_v": "3.0"}, status_code=200
                )

            for app in apps:
                app = app["data"]

                if search in app["title"]:
                    app["indexed"] = "name"
                    final.append(app)

                    continue
                elif ratio(search, app["name"]) >= 0.85:
                    app["indexed"] = "name_ratio"
                    ratio_info = {
                        "is_ratio": True,
                        "keyword": app["name"],
                        "confidence": ratio(search, app["name"]),
                    }
                    final.append(app)

                    continue

                for tag in app["tags"]:
                    if search in tag:
                        app["indexed"] = "tag"
                        final.append(app)

                        continue
                    elif ratio(search, tag) >= 0.85:
                        app["indexed"] = "tag_ratio"
                        ratio_info = {
                            "is_ratio": True,
                            "keyword": tag,
                            "confidence": ratio(search, tag),
                        }
                        final.append(app)

                        continue

            if final == []:
                return JSONResponse(
                    {"index": "no_results", "search_api_v": "3.0"}, status_code=200
                )

            return JSONResponse(
                {"index": final, "ratio_info": ratio_info, "search_api_v": "3.0"},
                status_code=200,
            )

        @self.router.get("/misc/get_prominent_color")
        async def get_prominent_color(image_url: str):
            if not is_dev:
                return get_color(BytesIO(httpx.get(image_url).content))
            else:
                # prevent vm IP leakage
                if not re.search(r"^https://tr\.rbxcdn\.com/.+", image_url):
                    return JSONResponse(
                        {"code": 400, "message": "URL must be to Roblox's CDN."},
                        status_code=400,
                    )

                return get_color(BytesIO(httpx.get(image_url).content))

        @self.router.post("/report-version")
        async def report_version(req: Request):
            json = await req.json()
            key = db.get(round(time.time() / 86400), db.REPORTED_VERSIONS)
            branch = str(json["branch"]).lower()

            if not json["version"] in accepted_versions:
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Unsupported version, please update Administer.",
                    },
                    status_code=400,
                )

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

            return JSONResponse(
                {"code": 200, "message": "Version has been recorded"}, status_code=200
            )

        @self.router.post("/app-config/upload")
        async def app_config(req: Request):
            config: {} = await req.json()
            id = config.get("Metadata", {}).get(
                "AdministerID", len(db.get_all(db.APPS))
            )
            existing = db.get(id, db.APPS) or default_app

            print(config)

    def initialize_content_routes(self):
        @self.asset_router.get("/ping")
        async def ping():
            return "OK"

        @self.asset_router.get("/{appid:int}")
        async def get_app(appid: int):
            try:
                app = request_app(appid)

                if app == None:
                    raise FileNotFoundError

                return JSONResponse(app, status_code=200)

            except (FileNotFoundError, OSError):
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "not-found",
                        "user_facing_message": "This asset wasn't found. Maybe it was deleted while you were viewing it?",
                    },
                    status_code=404,
                )

        @self.asset_router.put("/{asset_id}/vote")
        async def rate_app(req: Request, asset_id: str, payload: RatingPayload):
            if "RobloxStudio" in req.headers.get("user-agent"):
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "studio-restricted",
                        "user_facing_message": "Sorry, but this API endpoint may not be used in Roblox Studio. Please try it in a live game!",
                    },
                    status_code=400,
                )

            place = db.get(req.headers.get("Roblox-Id"), db.PLACES)
            rating = payload.vote == 1
            is_overwrite = False

            if not place:
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "bad-request",
                        "user_facing_message": "We can't find your game.",
                    },
                    status_code=400,
                )

            if asset_id not in place["apps"]:
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "bad-request",
                        "user_facing_message": "You have to install this app before you can rate it.",
                    },
                    status_code=400,
                )

            app = request_app(asset_id)
            if not app:
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "not-found",
                        "user_facing_message": "Could not find that app. Was it deleted?",
                    },
                    status_code=404,
                )

            if asset_id in place["ratings"]:
                print("Overwriting rating.")
                is_overwrite = True

                app["ratings"][
                    place["ratings"][asset_id]["rating"] == 1 and "likes" or "dislikes"
                ] -= 1
                place["ratings"][asset_id] = None

            place["ratings"][asset_id] = {
                "rating": rating,
                "owned": True,
                "timestamp": time.time(),
            }

            app["ratings"][rating and "likes" or "dislikes"] += 1

            db.set(asset_id, app, db.APPS)
            db.set(req.headers.get("Roblox-Id"), place, db.PLACES)

            return JSONResponse(
                {
                    "code": 200,
                    "message": f"success{is_overwrite and "_re-recorded" or ""}",
                    "user_facing_message": f"Your review has been recoded, thanks for voting!{is_overwrite and "We removed your previous rating for this asset."}",
                },
                status_code=200,
            )

        @self.asset_router.post("/{asset_id}/install")
        async def install_app(req: Request, asset_id: str):
            place = db.get(req.headers.get("Roblox-Id"), db.PLACES)

            if not place:
                place = {
                    "apps": [],
                    "ratings": {},
                    "start_ts": time.time(),  # make it easier to catch abusers
                    "start_source": (
                        "RobloxStudio" in req.headers.get("user-agent")
                        and "STUDIO"
                        or "RobloxApp" in req.headers.get("user-agent")
                        and "CLIENT"
                        or "UNKNOWN"
                    ),
                }

            app = request_app(asset_id)
            if not app:
                return JSONResponse(
                    {
                        "code": 404,
                        "message": "not-found",
                        "user_facing_message": "That isn't a valid asset. Did it get removed?",
                    },
                    status_code=404,
                )

            if asset_id in place["apps"]:
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "resource-limited",
                        "user_facing_message": "You may only install an asset once.",
                    },
                    status_code=400,
                )

            place["apps"].append(asset_id)
            app["downloads"] += 1

            db.set(asset_id, app, db.APPS)
            db.set(req.headers.get("Roblox-Id"), place, db.PLACES)

            src.downloads_today += 1

            return JSONResponse(
                {"code": 200, "message": "success", "user_facing_message": "Success!"},
                status_code=200,
            )


# @router.get("/logs/{logid:str}")
# def get_log(req: Request, logid: str):
#    return db.get(logid, db.LOGS)
