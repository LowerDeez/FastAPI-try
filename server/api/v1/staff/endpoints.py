from typing import List

from fastapi import APIRouter, Body, HTTPException, Path
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, DatabaseError

from .schemas import UserCreateSchema, UserReadSchema
from server.apps.staff.services import (
    create_new_random_user, get_users, create_user, get_user_by_id, delete_user, users_count
)
from server.shared.utils.database import get_db_session
from server.shared.api.responses import BadRequestJsonResponse, NotFoundJsonResponse


staff_api_router = APIRouter(
    dependencies=[
        # Depends(JWTAuthentication),
        # Depends(verify_token),
    ],
    tags=["Users"],
    prefix="/users"
)


@staff_api_router.get(
    "/test",
    name="users:test",
)
async def users_create_random_endpoint():
    session = await get_db_session()
    async with session():
        print("count", await users_count())
        print("users", await get_users())
    return {"success": True}


@staff_api_router.get(
    "/create-random",
    response_model=UserReadSchema,
    name="users:create-random",
)
async def users_create_random_endpoint():
    return await create_new_random_user()


@staff_api_router.get(
    "",
    response_model=List[UserReadSchema],
    name="users:list",
)
async def users_list_endpoint():
    return await get_users()


@staff_api_router.post(
    "",
    name="users:create",
    response_model=UserCreateSchema,
)
async def users_create_endpoint(
        user: UserCreateSchema = Body(
            ...,
            example={
                "first_name": "Gleb",
                "last_name": "Garanin",
                "username": "GLEF1X",
                "phone_number": "+7900232132",
                "email": "glebgar567@gmail.com",
                "password": "qwerty12345",
                "balance": 5,
            },
        ),
):
    """Create a new user in database"""
    payload = user.dict(exclude_unset=True)
    try:
        user = await create_user(**payload)
    except IntegrityError:
        return BadRequestJsonResponse(content="user with this username already exists")

    return user


@staff_api_router.get(
    "/{user_id}",
    response_model=UserReadSchema,
    name="users:get"
)
async def users_retrieve_endpoint(user_id: int = Path(...)):
    user = await get_user_by_id(user_id)
    try:
        return UserReadSchema.from_orm(user)
    except ValidationError:
        return NotFoundJsonResponse(content="user does not exist")


@staff_api_router.delete(
    "/{user_id}",
    response_description="return nothing",
    summary="Delete user from database",
    name="users:delete"
)
async def users_delete_endpoint(user_id: int = Path(...)):
    try:
        await delete_user(user_id=user_id)
    except DatabaseError:
        raise HTTPException(
            status_code=400, detail=f"There isn't entry with id={user_id}"
        )
    return {"message": f"User with id {user_id} was successfully deleted from database"}
