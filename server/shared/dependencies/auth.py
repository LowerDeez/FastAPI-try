from typing import Union, Literal, Protocol

from authlib.oauth2 import OAuth2Client


class PasswordHasher(Protocol):
    def hash(self, password: Union[str, bytes]) -> str: ...

    def verify(self, hash: Union[str, bytes], password: Union[str, bytes]) -> Literal[True]: ...

    def check_needs_rehash(self, hash: str) -> bool: ...


class OAuth(Protocol):
    ...
