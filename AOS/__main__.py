# pyxfluff 2024 - 2025

import il
import asyncio
import logging
import platform

from sys import argv
from pathlib import Path
from fastapi import FastAPI
from uvicorn import Config, Server

from AOS import __version__, is_dev, app, AOSError

if not is_dev:
    il.set_log_file(Path("/etc/adm/log"))
    logging.getLogger("uvicorn.error").disabled = True

def serve_web_server():
    il.cprint("[-] Loading Uvicorn...", 32)

    config = Config(app=app, host=argv[2], port=int(argv[3]), workers=8)

    logging.getLogger("uvicorn").disabled = True
    logging.getLogger("uvicorn.access").disabled = True

    il.cprint("[✓] Uvicorn loaded", 32)
    il.cprint("[-] Importing modules...", 32)

    from .routes.api import router as APIRouter, asset_router as AssetRouter
    from .routes.public_api import router as PublicRouter

    app.include_router(APIRouter, prefix="/api")
    app.include_router(AssetRouter, prefix="/api")

    app.include_router(PublicRouter, prefix="/pub")

    from .routes import frontend
    from . import middleware

    from .release_bot import bot, token

    asyncio.gather(bot.start(token))

    try:
        Server(config).run()
    except KeyboardInterrupt:
            il.cprint("[✓] Cleanup job OK", 31)

def help_command():
    pass


il.box(45, f"Administer App Server", f"v{__version__}")

if __name__ != "__main__":
    # il.cprint("AOS is running as a module, disregarding.", 31)
    #return
    pass

try:
    _ = argv[1]
except IndexError:
    help_command()
    raise AOSError("A command is required.")

match argv[1]:
    case "serve":
        try:
            serve_web_server()
        except IndexError:
            il.cprint("\n[x]: incorrect usage of `serve`\n\nusage: AOS serve [host] [port]", 31)

    case "help":
        help_command()

    case "usage":
        from AOS.reporting.GraphReporter import *

    case _:
        il.cprint("\n[x]: command not found, showing help", 31)
        help_command()

def main():
    # diseregard
    pass
