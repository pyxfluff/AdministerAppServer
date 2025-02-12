# pyxfluff 2024 - 2025

import il
import sys
import logging
import asyncio
import platform

from sys import argv
from fastapi import FastAPI
from uvicorn import Config, Server
from contextlib import asynccontextmanager

from builtins import BaseException

@asynccontextmanager
async def lifespan(app: FastAPI):
    il.cprint(
        f"[✓] Done! Serving {len(app.routes)} routes on http://{argv[2]}:{argv[3]}.",
        32,
    )
    try:
        yield
    finally:
        il.cprint("[✗] Goodbye, shutting things off...", 31)


class AOSVars:
    def __init__(self):
        self.version = "4.0.0"
        self.is_dev = True
        self.enable_bot_execution: True

        self.dbattrs = {
            "use_dev_db": False,
            "use_mock_db": False,
            "address": self.is_dev
            and "mongodb://mail.iipython.dev:27017"
            or "mongodb://127.0.0.1:27017",
            "timeout_ms": 15000,
        }

        self.security = {
            "use_roblox_lock": False,
            "use_api_keys": False,
            "use_sessions": False,
            "ratelimiting": {
                "max_reqs": 30,
                "reset_timeframe": 150,
                "max_incidents_before_block": 5,
            },
        }

        self.flags = {
            "v1x_cutoff": True,
            "beta_cli": True,
            "use_app_state": True,
            "is_v4_endpoints": True,
            "use_v4_jsons": True,
        }

        self.state = {
            "requests": 0,
            "default_app": {},
            "downloads_today": 0,
            "permitted_versions": ["2.0"],
            "unchecked_endpoints": [
                "logs",
                "css",
                "scss",
                "js",
                "img",
                "download-count",
                ".administer",
                "to",
            ],
        }


class AOSError(Exception):
    def __init__(self, message):
        il.cprint(message, 31)
        sys.exit(1)


globals = AOSVars()


def load_fastapi_app():
    app = FastAPI(
        debug=globals.is_dev,
        title=f"Administer App Server {globals.version}",
        description="An Administer app server instance for distributing Administer applications.",
        version=globals.version,
        openapi_url="/openapi",
        lifespan=lifespan,
    )

    config = Config(app=app, host=argv[2], port=int(argv[3]), workers=8)
    logging.getLogger("uvicorn").disabled = True
    logging.getLogger("uvicorn.access").disabled = True

    il.cprint("[✓] Uvicorn loaded", 32)
    il.cprint("[-] Importing modules...", 32)

    from .routes.backend import BackendAPI
    from .routes.public import PublicAPI
    from .routes.frontend import Frontend
    from .middleware import Middleware

    backend_api = BackendAPI(app)
    public_api = PublicAPI(app)

    backend_api.initialize_api_routes()
    backend_api.initialize_content_routes()
    public_api.initialize_routes()

    app.include_router(backend_api.router, prefix="/api")
    app.include_router(backend_api.asset_router, prefix="/api")
    app.include_router(public_api.router, prefix="/pub")

    frontend = Frontend(app)
    frontend.initialize_frontend()

    middleware = Middleware(app)

    from .release_bot import bot, token

    asyncio.gather(bot.start(token))

    try:
        Server(config).run()
    except KeyboardInterrupt:
        il.cprint("[✓] Cleanup job OK", 31)

    return app
