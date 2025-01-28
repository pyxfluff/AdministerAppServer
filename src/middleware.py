# pyxfluff 2024

from http import HTTPStatus
from il import request as log_req
from fastapi import Response, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import time
import httpx
import platform

from types import FunctionType
from collections import defaultdict

from src.database import db
import src

roblox_lock = src.is_dev

rate_limit_reqs = 30
rate_limit_reset = 150
rate_limit_max_incidents = 5

api_lock = False
enable_sessions = False

known_good_ips = []
limited_ips = defaultdict(list)
mem_incidents = defaultdict(list)
mem_blocked_ips = defaultdict(list)

blocked_users = db.get("__BLOCKED_USERS__", db.API_KEYS)
blocked_games = db.get("__BLOCKED__GAMES__", db.API_KEYS)
forbidden_ips = db.get("BLOCKED_IPS", db.ABUSE_LOGS) or []

auth_key = db.get("__ENV_AUTH__", db.SECRETS)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: FunctionType) -> Response:
        if request.headers.get("CF-Connecting-IP") in forbidden_ips:
            return JSONResponse(
                {
                    "code": 400,
                    "message": "Sorry, but your IP has been blocked due to suspected abuse. Please reach out if this was a mistake.",
                },
                status_code=400,
            )

        if (
            str(request.url).split("/")[3] == "app-config"
            and request.headers.get("X-Adm-Auth", "") == auth_key
        ):
            return await call_next(request)
        elif (
            str(request.url).split("/")[3] == "app-config"
            and request.headers.get("X-Adm-Auth", "") == ""
        ):
            return JSONResponse({"code": 401, "message": "Bad authorization."}, 401)

        if roblox_lock:
            if (
                request.url
                in [
                    "http://administer.notpyx.me/",
                    "https://administer.notpyx.me/",
                    "https://adm_unstable.notpyx.me/"
                    "http://127.0.0.1:8000/",
                ]
                or str(request.url).split("/")[3] in src.whitelist
            ):
                return await call_next(request)

            if (
                not request.headers.get("Roblox-Id")
                and not request.url == "http://administer.notpyx.me/"
            ):
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "This App Server is only accepting requests from Roblox game servers.",
                    },
                    status_code=400,
                )

            if request.headers.get("CF-Connecting-IP") in known_good_ips:
                # all is well
                return await call_next(request)

            elif "RobloxStudio" in request.headers.get("user-agent"):
                # Limit this on a per-API basis
                return await call_next(request)

            elif (
                not httpx.get(
                    f"http://ip-api.com/json/{request.headers.get("CF-Connecting-IP")}?fields=status,isp"
                ).json()["isp"]
                == "Roblox"
            ):
                db.set(
                    request.headers.get("CF-Connecting-IP"),
                    db.ABUSE_LOGS,
                    {
                        "timestamp": time.time(),
                        "ip-api_full_result": httpx.get(
                            f"http://ip-api.com/json/{request.headers.get("CF-Connecting-IP")}?fields=status,message,country,regionName,isp,org,mobile,proxy,hosting,query"
                        ).json(),
                        "roblox-id": request.headers.get("Roblox-Id"),
                        "user-agent": request.headers.get("user-agent", "unknown"),
                        "endpoint": request.url,
                    },
                )

                forbidden_ips.append(request.headers.get("CF-Connecting-IP"))
                db.set("BLOCKED_IPS", forbidden_ips, db.ABUSE_LOGS)

                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Your IP has been blocked due to suspected API abuse.",
                    },
                    status_code=401,
                )

            else:
                known_good_ips.append(request.headers.get("CF-Connecting-IP"))

        if api_lock and not request.headers.get("X-Administer-Key"):
            return JSONResponse(
                {"code": 400, "message": "A valid API key must be used."},
                status_code=401,
            )

        elif api_lock and not db.get(
            request.headers.get("X-Administer-Key"), db.API_KEYS
        ):
            return JSONResponse(
                {"code": 400, "message": "Please provide a valid API key."},
                status_code=401,
            )

        elif api_lock:
            api_key_data = db.get(request.headers.get("X-Administer-Key"), db.API_KEYS)

            if (
                api_key_data.disabled
                or api_key_data.registered_to in blocked_users
                or api_key_data.registered_game in blocked_games
            ):
                return JSONResponse(
                    {
                        "code": 400,
                        "message": "Your API key has been disabled due to possible abuse. To reach out to the API team please join the discord and make a ticket (/discord).",
                    },
                    status_code=400,
                )

        if enable_sessions and not request.headers.get("X-Administer-Session"):
            return JSONResponse(
                {"code": 400, "message": "A valid session token is required."},
                status_code=400,
            )

        return await call_next(request)


class RateLimiter(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: FunctionType) -> Response:
        cf_ip = request.headers.get("CF-Connecting-IP")

        if cf_ip in mem_blocked_ips:
            print("This IP is blocked in memory.")
            return Response(
                status_code=400,
                content="Sorry, you have been blocked. If you believe this is in error please reach out.",
            )

        if not cf_ip:
            # development install?
            src.requests += 1
            return await call_next(request)

        limited_ips[cf_ip] = [
            timestamp
            for timestamp in limited_ips[cf_ip]
            if timestamp > time.time() - rate_limit_reset
        ]

        if len(limited_ips[cf_ip]) >= rate_limit_reqs:
            print("Rate limit exceeded")
            return Response(
                status_code=429,
                content="Too many requests. Try again later. Do NOT refresh this page or else you will be blocked.",
            )

        limited_ips[cf_ip].append(time.time())

        src.requests += 1

        return await call_next(request)


class Logger(BaseHTTPMiddleware):
    async def dispatch(self, req: Request, call_next: FunctionType) -> Response:
        cf_ip = req.headers.get("CF-Connecting-IP")

        t = time.time()
        res = await call_next(req)

        log_req(
            str(req.url),
            req.headers.get("CF-Connecting-IP"),
            f"Code {res.status_code} ({HTTPStatus(res.status_code).phrase})",
            str(res.status_code).startswith("2") and 32 or 31,
            time.time() - t,
            f"PlaceID: {req.headers.get("Roblox-Id") or "Not a Roblox place"}",
            req.method,
        )

        return res


src.app.add_middleware(AuthMiddleware)
src.app.add_middleware(RateLimiter)
src.app.add_middleware(Logger)
