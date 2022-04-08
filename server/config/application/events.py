from typing import Callable, Coroutine, Any

from fastapi import FastAPI


# noinspection PyUnusedLocal
def create_on_startup_handler(app: FastAPI) -> Callable[..., Coroutine[Any, Any, None]]:
    async def on_startup() -> None:
        from ..infrastructure.databases.postgres import create_all, recreate
        await create_all(app.state.config.database.connection_uri)

    return on_startup


def create_on_shutdown_handler(app: FastAPI) -> Callable[..., Coroutine[Any, Any, None]]:
    async def on_shutdown() -> None:
        ...

    return on_shutdown
