from .config.settings import settings
from .config.application.builder import build_app
from .config.application.dev import DevelopmentApplicationBuilder
from .config.gunicorn_app import StandaloneApplication
# from src.utils.logging import LoggingConfig, configure_logging


def run_application() -> None:
    # stdlib_logconfig_dict = configure_logging(LoggingConfig())
    app = build_app(DevelopmentApplicationBuilder(config=settings))
    options = {
        "bind": "%s:%s" % (settings.application.host, settings.application.port),
        "worker_class": "uvicorn.workers.UvicornWorker",
        "reload": True,
        "disable_existing_loggers": False,
        "preload_app": True,
        # "logconfig_dict": stdlib_logconfig_dict
    }
    gunicorn_app = StandaloneApplication(app, options)
    gunicorn_app.run()


if __name__ == "__main__":
    run_application()
