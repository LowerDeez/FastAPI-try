from functools import partial, wraps
import typing

from sqlalchemy import lambda_stmt, select, update as sql_update, exists as sql_exists, delete as sql_delete, func
from sqlalchemy.dialects.postgresql import insert

from ..di import injector
from ..dependencies.database import AsyncDatabase

Model = typing.TypeVar("Model")
ASTERISK = "*"


def async_db_operation(function=None, *, callback=lambda value: value):
    if function is None:
        return partial(async_db_operation, callback=callback)

    @wraps(function)
    async def wrapper(*args, **kwargs):
        db = injector.get(AsyncDatabase)

        async with db.async_session() as session:
            stmt = await function(*args, **kwargs)
            result = await session.execute(stmt)
            result = callback(result)
            return result

    return wrapper


@async_db_operation(callback=lambda value: value.mappings().first())
async def create(model: Model, /, **values: typing.Any) -> Model:
    """Add model into database"""
    insert_stmt = insert(model).values(**values).returning(model)
    return insert_stmt


@async_db_operation(callback=lambda value: value.scalars().all())
async def select_all(model: Model, *clauses: typing.Any) -> typing.List[Model]:
    """
    Selecting data from table and filter by kwargs data

    :param model:
    :param clauses:
    :return:
    """
    stmt = lambda_stmt(lambda: select(model))
    stmt += lambda s: s.where(*clauses)
    return stmt


@async_db_operation(callback=lambda value: value.scalars().first())
async def select_one(model: Model, *clauses: typing.Any) -> Model:
    """
    Return scalar value
    """
    stmt = lambda_stmt(lambda: select(model))
    stmt += lambda s: s.where(*clauses)
    return stmt


@async_db_operation(callback=lambda value: None)
async def update(model: Model, *clauses: typing.Any, **values: typing.Any) -> None:
    stmt = sql_update(model).where(*clauses).values(**values).returning(None)
    return stmt


@async_db_operation(callback=lambda value: value.scalar())
async def exists(model: Model, *clauses: typing.Any) -> typing.Optional[bool]:
    stmt = sql_exists(select(model).where(*clauses)).select()
    return stmt


@async_db_operation(callback=lambda value: value.mappings().all())
async def delete(model: Model, *clauses: typing.Any) -> typing.List[Model]:
    stmt = sql_delete(model).where(*clauses).returning(ASTERISK)
    return stmt


@async_db_operation(callback=lambda value: value.scalars().first())
async def count(model: Model) -> int:
    stmt = func.count(model.id)
    return stmt
