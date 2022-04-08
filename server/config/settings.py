import pathlib
from typing import Any, Dict, List

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, validator

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent


def _make_fastapi_instance_kwargs(app_settings: "ApplicationSettings") -> Dict[str, Any]:
    return {
        "debug": app_settings.debug,
        "title": app_settings.project_name,
        "version": app_settings.version,
        "docs_url": app_settings.docs_prefix,
        "redoc_url": app_settings.redoc_prefix,
        "openapi_url": app_settings.openapi_root,
    }


class DatabaseSettings(BaseSettings):
    username: str = "postgres"
    password: str = "postgres"
    host: str = "pg_database"
    port: int = 5432
    name: str = "db"
    dialect: str = "postgresql+asyncpg"
    connection_uri: PostgresDsn | None = None

    @validator('connection_uri', pre=True)
    def assemble_db_connection(
        cls, value: str | None, values: Dict[str, Any]  # noqa: N805, WPS110
    ) -> str:
        if isinstance(value, str):
            return value

        return PostgresDsn.build(
            scheme=values.get('dialect'),
            user=values.get('username'),
            password=values.get('password'),
            host=values.get('host'),
            port=str(values.get('port')),
            path='/{0}'.format(values.get('name')),
        )

    class Config:
        env_prefix = "DB_"


class RabbitMQSettings(BaseSettings):
    uri: str = "amqp://test:test@rabbitmq"

    class Config:
        env_prefix = "RABBIT_MQ_"


class ApplicationSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: str = "8080"
    debug: bool = True
    api_prefix: str = '/api'
    docs_prefix: str = '/docs'
    redoc_prefix: str = '/redoc'
    openapi_root: str = "/openapi.json"
    admin: str = '/admin'
    startup: str = 'startup'
    secret_key: str = "change me"
    flask_admin_swatch: str = 'cerulean'

    project_name: str = 'FastAPI'
    description: str = 'FastAPI clean architecture'
    version: str = '0.1'

    swagger_ui_parameters: Dict[str, Any] = {
        'displayRequestDuration': True,
        'filter': True,
    }

    allowed_headers: List[str] = [
        "Content-Type",
        "Authorization",
        "accept",
        "Accept-Encoding",
        "Content-Length",
        "Origin",
    ]

    backend_cors_origins: List[AnyHttpUrl] = ["http://localhost", "http://localhost:4200", "http://localhost:3000"]

    db: DatabaseSettings = DatabaseSettings()

    class Config:
        case_sensitive = False


class Config(BaseSettings):
    database: DatabaseSettings = DatabaseSettings()
    application: ApplicationSettings = ApplicationSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()

    class Config:
        env_file = '.env'


def configure_initial_settings() -> Config:
    load_dotenv()

    return Config()


settings = configure_initial_settings()
