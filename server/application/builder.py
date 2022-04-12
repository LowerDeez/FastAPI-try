import abc

from fastapi import FastAPI

from server.config.settings import Settings


class BaseFastAPIApplicationBuilder(abc.ABC):
    app: FastAPI

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @abc.abstractmethod
    def configure_openapi_schema(self) -> None:
        pass

    @abc.abstractmethod
    def setup_middlewares(self) -> None:
        pass

    @abc.abstractmethod
    def configure_routes(self) -> None:
        pass

    @abc.abstractmethod
    def configure_exception_handlers(self) -> None:
        pass

    @abc.abstractmethod
    def configure_application_dependencies(self) -> None:
        pass

    @abc.abstractmethod
    def configure_events(self) -> None:
        pass


def build_app(builder: BaseFastAPIApplicationBuilder) -> FastAPI:
    builder.configure_routes()
    builder.setup_middlewares()
    builder.configure_application_dependencies()
    builder.configure_exception_handlers()
    # We run `configure_events(...)` in the end of configure method, because we need to pass to on_shutdown and
    # on_startup handlers configured application
    builder.configure_events()
    return builder.app
