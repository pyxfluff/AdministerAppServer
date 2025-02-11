# pyxfluff 2024
from .database import db

def request_app(app_id):
    return db.get(app_id, db.APPS)
