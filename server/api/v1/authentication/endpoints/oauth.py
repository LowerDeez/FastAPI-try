from authlib.integrations.base_client import OAuthError
from fastapi import Depends, APIRouter
from starlette.requests import Request
from starlette.responses import RedirectResponse, HTMLResponse

from .login import auth_api_router
from server.shared.di import injector
from server.shared.dependencies.auth import OAuth

oauth_api_router = APIRouter(prefix="/oauth")
auth_api_router.include_router(oauth_api_router)


@oauth_api_router.get("/google/login")
async def google_login(request: Request):
    oauth = injector.get(OAuth)
    redirect_uri = oauth_api_router.url_path_for("oauth:google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@oauth_api_router.get('/google/auth', name="google:oauth")
async def google_auth(request: Request):
    oauth = injector.get(OAuth)

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    # user = await oauth.google.parse_id_token(request, token)
    user = await oauth.google.parse_id_token(request, token)
    request.session['user'] = dict(user)
    return RedirectResponse(url='/')
