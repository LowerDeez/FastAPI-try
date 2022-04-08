from functools import partial, wraps
import typing

from sqlalchemy import lambda_stmt, select, update, exists, delete, func
from sqlalchemy.dialects.postgresql import insert

from ..di import injector
from ..dependencies.database import AsyncDatabase

Model = typing.TypeVar("Model")


def async_db_operation(function=None, *, callback=lambda value: value):
    if function is None:
        return partial(async_db_operation, callback=callback)

    @wraps(function)
    async def wrapper(*args, **kwargs):
        db = injector.get(AsyncDatabase)

        async with db.async_session() as session:
            stmt = await function(*args, **kwargs)
            result = await session.execute(stmt)
            return callback(result)

    return wrapper


@async_db_operation(callback=lambda value: value.mappings().first())
async def create(model: Model, /, **values: typing.Any) -> Model:
    """Add model into database"""
    insert_stmt = insert(model).values(**values).returning(model)
    return insert_stmt


@async_db_operation(callback=lambda value: value.scalars().all())
async def select_all(model: Model, *clauses: typing.Any) -> typing.List[Model]:
    stmt = lambda_stmt(lambda: select(model))
    stmt += lambda s: s.where(*clauses)
    return stmt
