from typing import List
from pydantic import BaseModel


class Entity(BaseModel):
    text: str
    start: int
    end: int
    probability: float