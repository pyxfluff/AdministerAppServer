# pyxfluff 2024

import il
import logging
import platform

from pathlib import Path
from fastapi import FastAPI

# meta
__version__ = "3.1"
requests = 0
downloads_today = 0
is_dev = "zen" in platform.release() # TODO: More robust detection system; not *every* dev instance will be Linux Zen.
accepted_versions = ["1.1.1", "1.2", "1.2.1", "1.2.2", "1.2.3", "2.0"]
whitelist = ["logs", "css", "scss", "js", "img", "download-count", ".administer", "to"]
# default_app = { Metadata: {GeneratedAt: int, UpdatedAt: int, AppAPIPreferredVersion: int, AppVersion: number, IsOld: bool, AdministerID: number }, Developer: {  }}
default_app = {  }

if not is_dev:
    il.set_log_file(Path("/etc/adm/log"))
    logging.getLogger("uvicorn.error").disabled = True

il.box(30, f"Administer App Server {__version__}", "")
il.cprint("[-] Loading Uvicorn...", 32)
app = FastAPI(
    # Meta
    debug=is_dev,
    title=f"Administer App Server {__version__}",
    description="An Administer app server instance for distributing Administer applications.",
    version=__version__,

    # Disable docs
    openapi_url=None
)

logging.getLogger("uvicorn").disabled = True
logging.getLogger("uvicorn.access").disabled = True

il.cprint( f"[✓] Uvicorn loaded", 32)
il.cprint(f"[-] Importing modules...", 32)

from .routes import api, frontend, public_api
from . import middleware

il.cprint("[✓] Done! This app server is now being served on http://0.0.0.0:8000.", 32)
