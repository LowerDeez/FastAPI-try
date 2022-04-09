from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException

from .schemas import UserDTO
from server.apps.authentication.sequrity.authentication import JWTAuthentication
from server.apps.staff.services import create_new_random_user, get_users


staff_api_router = APIRouter(
    dependencies=[
        Depends(JWTAuthentication),
        # Depends(verify_token),
    ],
    tags=["Users"],
    prefix="/users"
)


@staff_api_router.get(
    "/all",
    response_model=List[UserDTO],
    name="users:all",
)
async def get_all_users_endpoint():
    return await get_users()


@staff_api_router.get(
    "/create-random",
    response_model=UserDTO,
    name="users:create-random",
)
async def create_random_user_endpoint():
    return await create_new_random_user()
