import pytest
from typing import AsyncContextManager, Awaitable, Callable
from fastapi import FastAPI
from httpx import AsyncClient

from server.apps.staff.models import User
from server.apps.staff.services import get_users, users_count, create_new_random_user, get_user_by_id

pytestmark = [pytest.mark.asyncio]


async def test_simple(db_session: Callable[..., AsyncContextManager], test_user: Callable[..., Awaitable[User]]):
    async with db_session():
        test = await test_user()
        user = await create_new_random_user()
        assert (await users_count()) == 2
        assert (await get_users())[0].id == test.id
        assert (await get_users())[1].id == user.id


async def test_users_list_endpoint(
        db_session: Callable[..., AsyncContextManager],
        authorized_client: Callable[..., Awaitable[AsyncClient]],
        token: Callable[..., Awaitable[User]],
        test_user: Callable[..., Awaitable[User]],
        app: FastAPI
) -> None:
    print(app.url_path_for("users:list"))
    async with db_session():
        client = await authorized_client(await token(await test_user()))
        response = await client.get(app.url_path_for("users:list"))
        print(response.json())
        assert response.status_code == 200


# async def test_users_create_endpoint(authorized_client: AsyncClient, app: FastAPI) -> None:
#     response = await authorized_client.put(
#         app.url_path_for("users:create"),
#         json={
#             "first_name": "first",
#             "last_name": "last",
#             "username": "username",
#             "phone_number": "+1111111111",
#             "email": "email-username@gmail.com",
#             "password": "password",
#             "balance": 5,
#         },
#     )
#     assert response.status_code == 200
#     print(response.json())
#     # assert response.json().get("success") is True
#
#
# async def test_users_retrieve_endpoint(authorized_client: AsyncClient, app: FastAPI, test_user: User) -> None:
#     response = await authorized_client.get(app.url_path_for("users:get", user_id=str(test_user.id)))
#     assert response.status_code == 200
#
#
# async def test_users_delete_endpoint(authorized_client: AsyncClient, app: FastAPI, test_user: User) -> None:
#     response = await authorized_client.delete(app.url_path_for("users:delete_user", user_id=str(test_user.id)))
#     assert response.status_code == 200
#     assert response.json() == {"message": f"UserDTO with id {test_user.id} was successfully deleted from database"}
