from decimal import Decimal
from random import randint
import typing

from server.apps.staff.models import User
from server.shared.utils.database import Model, select_all, create, select_one, update, delete, count
from server.shared.di import injector
from server.shared.dependencies.auth import PasswordHasher


async def create_new_random_user() -> Model:
    hasher: PasswordHasher = injector.get(PasswordHasher)
    password_hash = hasher.hash("password")
    return await create(User, **{
            "first_name": "First name",
            "last_name": "Last name",
            "phone_number": "+1234567890",
            "email": f"test@test-{randint(1, 10000000000)}.com",
            "username": f"username-{randint(1, 10000000000)}",
            "password_hash": password_hash,
        })


async def create_user(
        *,
        first_name: str,
        last_name: str,
        phone_number: str,
        email: str,
        password: str,
        balance: typing.Union[Decimal, float, None] = None,
        username: typing.Optional[str] = None
) -> Model:
    hasher: PasswordHasher = injector.get(PasswordHasher)
    password_hash = hasher.hash(password)
    return await create(
        User,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        email=email,
        password_hash=password_hash,
        balance=balance,
        username=username,
    )


async def get_users(*clauses: typing.Any) -> typing.List[Model]:
    return await select_all(User, *clauses)


async def get_user_by_username(username: str):
    return await select_one(User, User.username == username)


async def get_user_by_id(user_id: int):
    return await select_one(User, User.id == user_id)


async def update_password_hash(password_hash: str, user_id: int) -> None:
    await update(User, User.id == user_id, password_hash=password_hash)


async def delete_user(user_id: int):
    return await select_one(User, User.id == user_id)


async def users_count() -> int:
    return await count(User)
