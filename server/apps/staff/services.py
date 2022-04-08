from random import randint
import typing

from server.apps.staff.models import User
from server.shared.utils.database import select_all, create


async def get_new_user():
    return await create(User, **{
            "first_name": "First name",
            "last_name": "Last name",
            "phone_number": "+1234567890",
            "email": f"test@test-{randint(1, 10000000000)}.com",
            "username": f"username-{randint(1, 10000000000)}",
            "password_hash": "password",
        })


async def get_users(*clauses: typing.Any):
    return await select_all(User, *clauses)
