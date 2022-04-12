import asyncio
from typing import Awaitable, cast, Callable, Any, AsyncGenerator, AsyncContextManager, Generator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from server.application import build_app
from server.application.dev import DevelopmentApplicationBuilder
from server.config.infrastructure.databases.postgres import AsyncDatabaseTestComponents
from server.config.settings import Settings
from server.apps.authentication.shortcuts import create_access_token_for_user
from server.apps.staff.models import User
from server.apps.staff.services import create_user
from server.shared.di import injector
from server.shared.dependencies.database import AsyncDatabase
from server.shared.utils.database import get_db_session

TEST_USERNAME = "username"
TEST_PASSWORD = "password"


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# @pytest.fixture(scope="session")
# def path_to_alembic_ini() -> str:
#     from server.config.settings import BASE_DIR  # local import only for tests
#     return str(BASE_DIR / "alembic.ini")
#
#
# @pytest.fixture(scope="session")
# def path_to_migrations_folder() -> str:
#     from server.config.settings import BASE_DIR  # local import only for tests
#     return str(BASE_DIR / "server" / "config" / "infrastructure" / "databases" / "migrations")
#
#
# @pytest.fixture(scope="session")
# async def apply_migrations(path_to_alembic_ini: str, path_to_migrations_folder: str) -> AsyncGenerator[None, Any]:
#     print(path_to_alembic_ini, path_to_migrations_folder)
#     alembic_cfg = alembic_config.Config(path_to_alembic_ini)
#     alembic_cfg.set_main_option('script_location', path_to_migrations_folder)
#     command.upgrade(alembic_cfg, 'head')
#     yield
#     command.downgrade(alembic_cfg, 'base')


@pytest.fixture(scope='module')
def app() -> FastAPI:
    settings = Settings()
    app = build_app(DevelopmentApplicationBuilder(settings=settings))
    injector.register(AsyncDatabase, AsyncDatabaseTestComponents)
    return app


@pytest.fixture(scope='module')
async def initialized_app(app: FastAPI) -> AsyncGenerator[FastAPI, Any]:
    """
    Programmatically send startup/shutdown lifespan events into ASGI applications.
    When used in combination with an ASGI-capable HTTP client such as HTTPX, this allows mocking or
    testing ASGI applications without having to spin up an ASGI server.
    """
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(initialized_app: FastAPI) -> AsyncGenerator[AsyncClient, Any]:
    async with AsyncClient(
            app=initialized_app,
            base_url="http://test",
            headers={"Content-Type": "application/json"},
    ) as client:  # type: AsyncClient
        yield client


@pytest.fixture(autouse=True)
async def db_session(initialized_app) -> Callable[..., AsyncContextManager]:  # type: ignore
    return await get_db_session()


@pytest.fixture
async def test_user(initialized_app) -> Callable:  # type: ignore
    return lambda: create_user(
        email="test@test.com",
        password=TEST_PASSWORD,
        username=TEST_USERNAME,
        first_name="Name",
        last_name="Lastname",
        phone_number="+7657676556",
        balance=666
    )


@pytest.fixture
async def token() -> Callable[..., Awaitable[User]]:
    return lambda user: create_access_token_for_user(user=user, password=TEST_PASSWORD)


@pytest.fixture(name="settings")
def application_settings_fixture(app: FastAPI) -> Settings:
    return cast(Settings, app.state.settings)


@pytest.fixture
async def authorized_client(client: AsyncClient) -> Callable[...,  Awaitable[AsyncClient]]:
    async def factory(token: str):
        client.headers = {
            "Authorization": f"Bearer {token}",
            **client.headers,
        }
        return client
    return factory
