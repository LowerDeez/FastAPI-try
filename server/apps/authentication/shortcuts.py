from fastapi.security import OAuth2PasswordRequestForm

from server.apps.authentication.sequrity.jwt.authentication import JWTLoginService
from server.apps.staff.models import User


async def create_access_token_for_user(user: User, password: str):
    jwt_service = JWTLoginService()
    return await jwt_service.authenticate_user(
        form_data=OAuth2PasswordRequestForm(username=user.username, password=password, scope="")
    )
