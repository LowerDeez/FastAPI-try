from copy import copy
from dataclasses import dataclass, field as dc_field
from datetime import datetime, timedelta
from typing import Any, Dict, NewType

from argon2.exceptions import VerificationError
import jwt
from fastapi import HTTPException, Header
from fastapi.security import SecurityScopes, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import ValidationError
from starlette import status
from starlette.requests import Request

from server.apps.authentication.sequrity.dto import TokenPayload
from server.apps.staff.models import User
from server.apps.staff.services import get_user_by_username, update_password_hash
from server.config.settings import Settings
from server.shared.di import injector
from server.shared.dependencies.auth import PasswordHasher
from server.shared.dependencies.settings import Settings as SettingsProtocol

JWTToken = NewType("JWTToken", str)


class UserIsUnauthorized(Exception):
    def __init__(self, message: str = "incorrect username or password"):
        self.message = message

    def __str__(self):
        return self.message


@dataclass
class JWTLoginService:
    password_hasher: PasswordHasher = dc_field(init=False)
    algorithm: str = dc_field(init=False)
    secret_key: str = dc_field(init=False)
    token_expires_in_minutes: float = dc_field(init=False)

    def __post_init__(self):
        settings: Settings = injector.get(SettingsProtocol)
        self.password_hasher = injector.get(PasswordHasher)
        self.algorithm = settings.security.jwt_algorithm
        self.secret_key = settings.security.jwt_secret_key
        self.token_expires_in_minutes = settings.security.jwt_access_token_expire_in_minutes

    async def authenticate_user(self, form_data: OAuth2PasswordRequestForm) -> JWTToken:
        if not (user := await get_user_by_username(str(form_data.username))):
            raise UserIsUnauthorized()

        if self.password_hasher.check_needs_rehash(user.password_hash):
            await update_password_hash(
                password_hash=self.password_hasher.hash(form_data.password),
                user_id=user.id
            )

        try:
            self.password_hasher.verify(user.password_hash, form_data.password)
        except VerificationError:
            raise UserIsUnauthorized()

        return JWTToken(self._generate_jwt_token({
            "sub": form_data.username,
            "username": form_data.username,
            "scopes": form_data.scopes,
        }))

    def _generate_jwt_token(self, token_payload: Dict[str, Any]) -> str:
        token_payload = {
            "exp": datetime.utcnow() + timedelta(minutes=self.token_expires_in_minutes),
            **token_payload
        }
        filtered_payload = {k: v for k, v in token_payload.items() if v is not None}
        return jwt.encode(filtered_payload, self.secret_key, algorithm=self.algorithm)


@dataclass
class JWTAuthenticationService:
    token_resolver: OAuth2PasswordBearer = dc_field(init=False)
    algorithm: str = dc_field(init=False)
    secret_key: str = dc_field(init=False)
    token_expires_in_minutes: float = dc_field(init=False)

    def __post_init__(self):
        settings: Settings = injector.get(SettingsProtocol)
        self.token_resolver = OAuth2PasswordBearer(
            tokenUrl=f"{settings.application.api_prefix}/v1/oauth",
            scopes={
                "me": "Read information about the current user.",
                "items": "Read items."
            },
        )
        self.algorithm = settings.security.jwt_algorithm
        self.secret_key = settings.security.jwt_secret_key
        self.token_expires_in_minutes = settings.security.jwt_access_token_expire_in_minutes

    async def __call__(self, request: Request, security_scopes: SecurityScopes) -> User:
        # FIXME: small hack to display authorization token in Swagger
        if not request.headers.get("Authorization"):
            headers = dict(request.headers)
            headers["Authorization"] = request.headers.get("authorization-")
            request._headers = headers

        jwt_token = await self.token_resolver(request)

        if jwt_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token is missing",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_payload = self._decode_token(token=jwt_token)

        for scope in security_scopes.scopes:
            if scope not in token_payload.scopes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="corresponding scopes to execute this operation are missing",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return await self._retrieve_user_or_raise_exception(token_payload.username)

    def _decode_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenPayload(username=payload["username"], scopes=payload.get("scopes", []))
        except (jwt.DecodeError, ValidationError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Input bearer token is incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def _retrieve_user_or_raise_exception(self, username: str) -> User:
        if user := await get_user_by_username(username=username):  # type: User
            return user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def JWTAuthentication(
        request: Request,
        security_scopes: SecurityScopes,
        authorization_: str = Header(None)  # hack to display header input in Swagger
):
    return await JWTAuthenticationService()(request, security_scopes)
