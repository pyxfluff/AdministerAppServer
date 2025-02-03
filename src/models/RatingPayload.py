# pyxfluff 2024

from pydantic import BaseModel

class RatingPayload(BaseModel):
    vote: int
    is_favorite: bool
