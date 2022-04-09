from fastapi import APIRouter

from .schemas import TestResponse


healthcheck_api_router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])


@healthcheck_api_router.get("", response_model=TestResponse)
async def test():
    return {"success": True}
