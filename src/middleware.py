# pyxfluff 2024

from fastapi import Response, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import time
import httpx
import platform

from types import FunctionType
from collections import defaultdict

from src.database import db
from src import app

roblox_lock = not "zen" in platform.release()

rate_limit_reqs = 30
rate_limit_reset = 150
rate_limit_max_incidents = 5

api_lock = False
enable_sessions = True

known_good_ips = []
limited_ips = defaultdict(list)
mem_incidents = defaultdict(list)
mem_blocked_ips = defaultdict(list)

blocked_users = db.get("__BLOCKED_USERS__", db.API_KEYS)
blocked_games = db.get("__BLOCKED__GAMES__", db.API_KEYS)
forbidden_ips = db.get("BLOCKED_IPS", db.ABUSE_LOGS) or []

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: FunctionType) -> Response:
        if request.headers.get("CF-Connecting-IP") in forbidden_ips:
            return JSONResponse({"code": 400, "message": "Sorry, but your IP has been blocked due to suspected abuse. Please reach out if this was a mistake."}, status_code=400)

        if roblox_lock:
            if request.url in ["http://administer.notpyx.me/", "https://administer.notpyx.me/", "http://127.0.0.1:8000/"] \
                    or str(request.url).split("/")[3] in ["logs", "css", "scss", "js", "img"]:
                return await call_next(request)
            
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
                    "timestamp": time.time(), 
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
            if timestamp > time.time() - rate_limit_reset
        ]

        if len(limited_ips[cf_ip]) >= rate_limit_reqs:
            return Response(status_code=429, content="Too many requests. Try again later. Do NOT refresh this page or else you will be blocked.")

        limited_ips[cf_ip].append(time.time())
        response = await call_next(request)
        return response
    
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimiter)