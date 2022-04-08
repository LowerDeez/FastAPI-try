from typing import Protocol


class PasswordHasherProto(Protocol):

    def hash(self, password: str) -> str: ...

    def check_needs_rehash(self, hashed: str) -> bool: ...

    def verify(self, hashed: str, password: str) -> bool: ...