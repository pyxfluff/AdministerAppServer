# pyxfluff 2024

from fastapi import FastAPI

# meta
__version__ = 3
requests = 0
downloads_today = 0

app = FastAPI()

from .routes import api, frontend, public_api
from . import middleware