# pyxfluff 2024 - 2025

import il
import asyncio
import logging
import platform

from sys import argv
from pathlib import Path
from fastapi import FastAPI
from uvicorn import Config, Server

from src import __version__, is_dev, app

if not is_dev:
    il.set_log_file(Path("/etc/adm/log"))
    logging.getLogger("uvicorn.error").disabled = True


il.box(45, f"Administer App Server", f"v{__version__}")
il.cprint("[-] Loading Uvicorn...", 32)

config = Config(app=app, host=argv[1], port=int(argv[2]))

logging.getLogger("uvicorn").disabled = True
logging.getLogger("uvicorn.access").disabled = True

il.cprint("[✓] Uvicorn loaded", 32)
il.cprint("[-] Importing modules...", 32)

from .routes.api import router as APIRouter
from .routes.public_api import router as PublicRouter

app.include_router(APIRouter, prefix="/api")

app.include_router(PublicRouter, prefix="/pub")

from .routes import frontend
from . import middleware

from .release_bot import bot, token
asyncio.gather(bot.start(token))

if __name__ == "__main__":
    Server(config).run()
