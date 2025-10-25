from typing import Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreateRequestSchema(BaseModel):
    """
    Модель для создания и обновления пользователя.
    Используется в POST и PUT запросах.
    """

    email: EmailStr = Field(description='Email пользователя')
    password: str = Field(
        min_length=8, description='Пароль (минимум 8 символов)'
    )
    role: Literal['buyer', 'seller'] = Field(
        default='buyer', description='Роль: "buyer" или "seller"'
    )


class UserResponseSchema(BaseModel):
    """
    Модель для ответа с данными пользователя.
    Используется в GET-запросах.
    """

    id: int = Field(description='Уникальный идентификатор пользователя')
    email: EmailStr = Field(description='Email пользователя')
    is_active: bool = Field(
        default=True,
        description='Активность пользователя (показывается или нет)',
    )
    role: Literal['buyer', 'seller', 'admin'] = Field(
        description='Роль пользователя'
    )

    model_config = ConfigDict(from_attributes=True)
