from fastapi import APIRouter

from server.config.settings import ApplicationSettings
from server.api.v1.authentication.endpoints.login import auth_api_router
from server.api.v1.healthcheck.endpoints import healthcheck_api_router
from server.api.v1.staff.endpoints import staff_api_router


def setup_routes_v1(app_settings: "ApplicationSettings"):
    api_router = APIRouter(prefix=f"{app_settings.api_prefix}/v1")

    api_router.include_router(healthcheck_api_router)
    api_router.include_router(staff_api_router)
    api_router.include_router(auth_api_router)

    return api_router
