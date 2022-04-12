from typing import Any, Optional, Dict, no_type_check

from argon2 import PasswordHasher as ArgonPasswordHasher
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .builder import BaseFastAPIApplicationBuilder
from .errors import http_error_handler, http422_error_handler
from .events import create_on_startup_handler, create_on_shutdown_handler
from .middlewares import add_process_time_header
from .routers import setup_routes_v1
from server.config.infrastructure.databases.postgres import DatabaseComponents, AsyncDatabaseComponents
from server.config.settings import make_fastapi_instance_kwargs, Settings
from server.apps.authentication.sequrity.oauth.integrations import OAUTH_INTEGRATIONS
from server.apps.authentication.sequrity.oauth.authentication import register_integrations
from server.shared.di import injector
from server.shared.dependencies.database import AsyncDatabase, Database
from server.shared.dependencies.settings import Settings
from server.shared.dependencies.auth import PasswordHasher, OAuth

ALLOWED_METHODS = ["POST", "PUT", "DELETE", "GET"]


class DevelopmentApplicationBuilder(BaseFastAPIApplicationBuilder):
    """Class, that provides the installation of FastAPI application"""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings=settings)
        self.app: FastAPI = FastAPI(
            **make_fastapi_instance_kwargs(app_settings=self._settings.application)
        )  # type: ignore
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

    def configure_exception_handlers(self) -> None:
        self.app.add_exception_handler(HTTPException, http_error_handler)
        self.app.add_exception_handler(RequestValidationError, http422_error_handler)

    def configure_application_dependencies(self) -> None:
        self.app.state.settings = self._settings
        injector.register(Settings, lambda: self._settings)
        injector.register(Database, DatabaseComponents)
        injector.register(AsyncDatabase, AsyncDatabaseComponents)
        injector.register(PasswordHasher, ArgonPasswordHasher)
        injector.register(OAuth, lambda: register_integrations(*OAUTH_INTEGRATIONS))

    def configure_events(self) -> None:
        self.app.add_event_handler("startup", create_on_startup_handler(self.app))
        self.app.add_event_handler("shutdown", create_on_shutdown_handler(self.app))
