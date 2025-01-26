# pyxfluff 2024 - 2025

import il
import platform

from sys import argv
from fastapi import FastAPI
from contextlib import asynccontextmanager

__version__ = "4.0.0-dev"
is_dev = (
    "zen" in platform.release()
)  # TODO: More robust detection system; not *every* dev instance will be Linux Zen.
accepted_versions = ["2.0"]

default_app = {}
requests = 0
downloads_today = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    il.cprint(
        f"[✓] Done! Serving {len(app.routes)} routes on http://{argv[1]}:{argv[2]}.",
        32,
    )
    try:
        yield
    finally:
        il.cprint("[✗] Goodbye, shutting things off...", 31)

app = FastAPI(
    # Meta
    debug=is_dev,
    title=f"Administer App Server {__version__}",
    description="An Administer app server instance for distributing Administer applications.",
    version=__version__,
    openapi_url="/openapi",
    lifespan=lifespan,
)
