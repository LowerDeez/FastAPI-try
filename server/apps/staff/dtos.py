from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class UserDTO(BaseModel):
    first_name: str = Field(..., example="Gleb", title="Имя")
    last_name: str = Field(..., example="Garanin", title="Фамилия")
    phone_number: Optional[str] = Field(
        None,
        # regex=r"^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$",
        min_length=0,
        max_length=15,
        title="Номер мобильного телефона",
        example="+7900232132",
    )
    email: EmailStr = Field(
        ..., title="Адрес электронной почты", example="glebgar567@gmail.com"
    )
    balance: float
    id: Optional[int] = None
    username: str = Field(..., example="GLEF1X")

    class Config:
        orm_mode = True
