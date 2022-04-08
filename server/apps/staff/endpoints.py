from typing import List

from fastapi import Path, HTTPException, Depends, APIRouter

from .dtos import UserDTO
from .services import get_new_user, get_users


staff_api_router = APIRouter(
    dependencies=[
        # Depends(SecurityGuardServiceDependencyMarker)
    ]
)


# noinspection PyUnusedLocal
@staff_api_router.get(
    "/users/all",
    response_model=List[UserDTO],
    # responses={400: {"model": DefaultResponse}},
    tags=["Users"],
    name="users:get_all_users"
)
async def get_all_users():
    # await get_new_user()
    return await get_users()
