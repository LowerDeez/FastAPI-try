from typing import Any, Optional, Dict, no_type_check

from argon2 import PasswordHasher as ArgonPasswordHasher
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .builder import BaseFastAPIApplicationBuilder
from .errors import http_error_handler
from .events import create_on_startup_handler, create_on_shutdown_handler
from .middlewares import add_process_time_header
from .routers import setup_routes_v1
from ..infrastructure.databases.postgres import DatabaseComponents, AsyncDatabaseComponents
from ..settings import _make_fastapi_instance_kwargs, Settings
from ...shared.di import injector
from ...shared.dependencies.database import AsyncDatabase, Database
from ...shared.dependencies.settings import Settings
from ...shared.dependencies.auth import PasswordHasher

ALLOWED_METHODS = ["POST", "PUT", "DELETE", "GET"]


class DevelopmentApplicationBuilder(BaseFastAPIApplicationBuilder):
    """Class, that provides the installation of FastAPI application"""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings=settings)
        self.app: FastAPI = FastAPI(**_make_fastapi_instance_kwargs(app_settings=self._settings.application))  # type: ignore
        self.app.config = self._settings  # type: ignore
        self._openapi_schema: Optional[Dict[str, Any]] = None

    def configure_openapi_schema(self) -> None:
        self._openapi_schema = get_openapi(
            title=self._settings.application.project_name,
            version=self._settings.application.version,
            description=self._settings.application.description,
            routes=self.app.routes,
        )
        self._openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        self.app.openapi_schema = self._openapi_schema

    @no_type_check
    def setup_middlewares(self):
        self.app.add_middleware(BaseHTTPMiddleware, dispatch=add_process_time_header)
        self.app.add_middleware(
            middleware_class=CORSMiddleware,
            allow_origins=self._settings.application.backend_cors_origins,
            allow_credentials=True,
            allow_methods=ALLOWED_METHODS,
            allow_headers=self._settings.application.allowed_headers,
            expose_headers=["User-Agent", "Authorization"],
        )
        self.app.add_middleware(
            middleware_class=SessionMiddleware,
            secret_key=self._settings.application.secret_key
        )

    @no_type_check
    def configure_routes(self):
        self.app.include_router(setup_routes_v1(self._settings.application))

    def configure_events(self) -> None:
        self.app.add_event_handler("startup", create_on_startup_handler(self.app))
        self.app.add_event_handler("shutdown", create_on_shutdown_handler(self.app))

    def configure_exception_handlers(self) -> None:
        self.app.add_exception_handler(HTTPException, http_error_handler)

    def configure_application_state(self) -> None:
        # db_components = DatabaseComponents(self._config.database.connection_uri)
        # do gracefully dispose engine on shutdown application
        # self.app.state.db_components = db_components
        self.app.state.settings = self._settings
        injector.register(Database, DatabaseComponents)
        injector.register(AsyncDatabase, AsyncDatabaseComponents)
        injector.register(Settings, lambda: self._settings)
        injector.register(PasswordHasher, ArgonPasswordHasher)

        # pwd_hasher = PasswordHasher()
        # rmq_service = RabbitMQService(
        #     self._config.rabbitmq.uri,
        #     Consumer(name="send_email", callback=send_email)
        # )

        # async def rmq_service_spin_up():
        #     async with rmq_service as rpc:
        #         yield rpc

        # self.app.dependency_overrides.update(
        #     {
        #         UserRepositoryDependencyMarker: lambda: UserRepository(
        #             db_components.sessionmaker, pwd_hasher
        #         ),
        #         ProductRepositoryDependencyMarker: lambda: ProductRepository(db_components.sessionmaker),
        #         OAuthServiceDependencyMarker: lambda: OAuthSecurityService(
        #             StarletteConfig(BASE_DIR / ".env"),
        #             OAuthIntegration(
        #                 name='google',
        #                 overwrite=False,
        #                 kwargs=dict(
        #                     server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        #                     client_kwargs={
        #                         'scope': 'openid email profile'
        #                     }
        #                 )
        #             )
        #         ),
        #         SecurityGuardServiceDependencyMarker: lambda: JWTSecurityGuardService(
        #             oauth2_scheme=OAuth2PasswordBearer(
        #                 tokenUrl="/api/v1/oauth",
        #                 scopes={
        #                     "me": "Read information about the current user.",
        #                     "items": "Read items."
        #                 },
        #             ),
        #             user_repository=UserRepository(db_components.sessionmaker, pwd_hasher),
        #             password_hasher=pwd_hasher,
        #             secret_key=self._config.server.security.jwt_secret_key,
        #             algorithm="HS256"
        #         ),
        #         ServiceAuthorizationDependencyMarker: lambda: JWTAuthenticationService(
        #             user_repository=UserRepository(db_components.sessionmaker, pwd_hasher),
        #             password_hasher=pwd_hasher,
        #             secret_key=self._config.server.security.jwt_secret_key,
        #             algorithm="HS256",
        #             token_expires_in_minutes=self._config.server.security.jwt_access_token_expire_in_minutes
        #         ),
        #         RPCDependencyMarker: rmq_service_spin_up
        #     }
        # )
