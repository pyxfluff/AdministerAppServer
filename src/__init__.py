# pyxfluff 2024

import il
import logging
from fastapi import FastAPI

# meta
__version__ = "3.1"
requests = 0
downloads_today = 0

il.box(30, f"Administer App Server {__version__}", "")
il.cprint("[-] Loading Uvicorn...", 32)
app = FastAPI(
    # Meta
    debug=False,
    title=f"Administer App Server {__version__}",
    description="An Administer app server instance for distributing Apps.",
    version=__version__,

    # Disable docs
    openapi_url=None
)

il.cprint( f"[✓] Uvicorn loaded", 32)
logging.getLogger("uvicorn").disabled = True
logging.getLogger("uvicorn.error").disabled = True
logging.getLogger("uvicorn.access").disabled = True
il.cprint(f"[-] Importing modules...", 32)

from .routes import api, frontend, public_api
from . import middleware

il.cprint("[✓] Done! This app server is now being served on http://0.0.0.0:8000.", 32)