# pyxfluff 2024

from fastapi import FastAPI

__version__ = 3

app = FastAPI()

from .routes import api, frontend, public_api
from . import middleware