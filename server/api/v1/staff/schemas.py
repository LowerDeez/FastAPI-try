from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class UserCreateSchema(BaseModel):
    first_name: str = Field(example="Name", title="Name")
    last_name: str = Field(example="Lastname", title="Lastname")
    phone_number: Optional[str] = Field(
        None,
        regex=r"^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$",
        min_length=0,
        max_length=15,
        title="Phone number",
        example="+1111111111",
    )
    email: EmailStr = Field(title="Email", example="username@gmail.com")
    balance: float
    id: Optional[int] = None
    username: str = Field(example="username")
    password: str = Field(example="qwerty12345")

    class Config:
        orm_mode = True


class UserReadSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone_number: str
    email: EmailStr
    balance: float
    username: str

    class Config:
        orm_mode = True
