import contextlib
from typing import AsyncGenerator, Callable, Protocol

from sqlalchemy.orm import Session


class Database(Protocol):
    def session(self) -> Callable[..., contextlib.AbstractContextManager[Session]]:
        ...


class AsyncDatabase(Protocol):
    async def async_session(self) -> AsyncGenerator:
        ...
