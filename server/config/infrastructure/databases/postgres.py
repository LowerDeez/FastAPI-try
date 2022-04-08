import contextlib
import logging
from typing import AsyncGenerator, Callable, Optional, cast, Type, Dict, Any
from sqlalchemy import inspect, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncSessionTransaction
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.orm.decl_api import (
    registry,
    DeclarativeMeta,
    declared_attr,
    has_inherited_table
)
from sqlalchemy.util import ImmutableProperties

from ...settings import settings

logger = logging.getLogger("sqlalchemy.execution")

mapper_registry = registry()
ASTERISK = "*"


async def create_all(connection_uri: str) -> None:
    """
    Should be executed before doing alembic migrations
    :param connection_uri:
    :return:
    """
    engine = create_async_engine(connection_uri, pool_pre_ping=True, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def recreate(connection_uri: str) -> None:
    engine = create_async_engine(connection_uri, pool_pre_ping=True, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        # await conn.run_sync(Base.metadata.create_all)


class Base(metaclass=DeclarativeMeta):
    """Declarative meta for mypy"""

    __abstract__ = True
    __mapper_args__ = {"eager_defaults": True}

    # these are supplied by the sqlalchemy-stubs or sqlalchemy2-stubs, so may be omitted
    # when they are installed
    registry = mapper_registry
    metadata = mapper_registry.metadata

    @declared_attr
    def __tablename__(self) -> Optional[str]:
        if not has_inherited_table(cast(Type[Base], self)):
            return cast(Type[Base], self).__qualname__.lower() + "s"
        return None

    def _get_attributes(self) -> Dict[Any, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def __str__(self) -> str:
        attributes = "|".join(str(v) for k, v in self._get_attributes().items())
        return f"{self.__class__.__qualname__} {attributes}"

    def __repr__(self) -> str:
        table_attrs = cast(ImmutableProperties, inspect(self).attrs)
        primary_keys = " ".join(
            f"{key.name}={table_attrs[key.name].value}"
            for key in inspect(self.__class__).primary_key
        )
        return f"{self.__class__.__qualname__}->{primary_keys}"

    def as_dict(self) -> Dict[Any, Any]:
        return self._get_attributes()


class DatabaseComponents:
    def __init__(self) -> None:
        self.connection_uri = settings.database.connection_uri
        engine = create_engine(
            self.connection_uri.replace('+asyncpg', ''),
            pool_pre_ping=True,
            future=True,
            echo=True,
        )
        self.session_factory = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    @contextlib.contextmanager
    def session(self) -> Callable[..., contextlib.AbstractContextManager[Session]]:
        session: Session = self.session_factory()
        try:
            yield session
        except Exception:
            logger.exception("Session rollback because of exception")
            session.rollback()
            raise
        finally:
            session.close()


class AsyncDatabaseComponents:
    def __init__(self) -> None:
        self.connection_uri = settings.database.connection_uri
        engine = create_async_engine(url=self.connection_uri, pool_pre_ping=True, future=True)
        self.session: AsyncSession = sessionmaker(  # NOQA
            engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )

    @contextlib.asynccontextmanager
    async def async_session(self) -> AsyncGenerator:
        """Yield an :class:`_asyncio.AsyncSessionTransaction` object."""
        async with self.session() as session:
            if not session.in_transaction() and session.is_active:
                async with session.begin():
                    yield session
            else:
                yield  # type: ignore
