from typing import Optional

from pydantic import BaseModel, Field


class TestResponse(BaseModel):
    success: bool = True
    user_agent: Optional[str] = Field(None, alias="User-Agent")
