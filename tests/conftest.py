"""
In conftest.py I mark most scope of fixtures as "module",
because performance if migrations will be executed for each function(by default) will be poor.
"""
import asyncio
from typing import cast, Any, AsyncGenerator

import pytest
from alembic import config as alembic_config, command
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from fastapi.security import SecurityScopes, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from httpx import AsyncClient, Headers
from sqlalchemy.orm import sessionmaker

from server.config.application.builder import build_app
from server.config.application.dev import DevelopmentApplicationBuilder
from server.config.settings import Settings
from server.apps.staff.models import User
from server.apps.staff.services import create_user
from server.apps.authentication.sequrity.authentication import JWTLoginService

TEST_PASSWORD = "password"


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def path_to_alembic_ini() -> str:
    from server.config.settings import BASE_DIR  # local import only for tests
    return str(BASE_DIR / "alembic.ini")


@pytest.fixture(scope="module")
def path_to_migrations_folder() -> str:
    from server.config.settings import BASE_DIR  # local import only for tests
    return str(BASE_DIR / "server" / "config" / "infrastructure" / "databases" / "migrations")


@pytest.fixture(scope="module")
async def apply_migrations(path_to_alembic_ini: str, path_to_migrations_folder: str) -> AsyncGenerator[None, Any]:
    alembic_cfg = alembic_config.Config(path_to_alembic_ini)
    alembic_cfg.set_main_option('script_location', path_to_migrations_folder)
    command.upgrade(alembic_cfg, 'head')
    yield
    command.downgrade(alembic_cfg, 'base')


@pytest.fixture(scope="module")
def app(apply_migrations: None) -> FastAPI:
    settings = Settings()
    app = build_app(DevelopmentApplicationBuilder(settings=settings))
    return app


@pytest.fixture(scope="module")
async def initialized_app(app: FastAPI) -> AsyncGenerator[FastAPI, Any]:
    """
    Programmatically send startup/shutdown lifespan events into ASGI applications.
    When used in combination with an ASGI-capable HTTP client such as HTTPX, this allows mocking or
    testing ASGI applications without having to spin up an ASGI server.
    """
    async with LifespanManager(app):
        yield app


@pytest.fixture(scope="module")
async def client(initialized_app: FastAPI) -> AsyncGenerator[AsyncClient, Any]:
    async with AsyncClient(
            app=initialized_app,
            base_url="http://test",
            headers={"Content-Type": "application/json"},
    ) as client:  # type: AsyncClient
        yield client


@pytest.fixture(scope="module")
async def test_user(session_maker: sessionmaker) -> User:  # type: ignore
    return await create_user(
        email="test@test.com",
        password=TEST_PASSWORD,
        username="username",
        first_name="Name",
        last_name="Lastname",
        phone_number="+7657676556",
        balance=666
    )


@pytest.fixture(scope="module")
def token(test_user: User) -> str:
    jwt_service = JWTLoginService()
    return await jwt_service.authenticate_user(
        form_data=OAuth2PasswordRequestForm(username=test_user.username, password=TEST_PASSWORD)
    )


@pytest.fixture(name="settings", scope="module")
def application_settings_fixture(app: FastAPI) -> Settings:
    return cast(Settings, app.state.settings)


@pytest.fixture(scope="module")
def authorized_client(client: AsyncClient, token: str) -> AsyncClient:
    client.headers = Headers({"Authorization": f"Bearer {token}"})
    return client
