from typing import List

from pydantic import BaseModel


class TokenPayload(BaseModel):
    username: str
    scopes: List[str] = []