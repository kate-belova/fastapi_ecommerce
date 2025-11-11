from decimal import Decimal
from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, Field, ConfigDict


class ProductCreateRequestSchema(BaseModel):
    """
    Модель для создания и обновления товара.
    Используется в POST и PUT запросах.
    """

    name: str = Field(
        min_length=3,
        max_length=100,
        description='Название товара (3-100 символов)',
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description='Описание товара (до 500 символов)',
    )
    price: Decimal = Field(gt=0, description='Цена товара (больше 0)')
    stock: int = Field(
        ge=0, description='Количество товара на складе (0 или больше)'
    )
    category_id: int = Field(
        description='ID категории, к которой относится товар'
    )

    @classmethod
    def as_form(
        cls,
        name: Annotated[str, Form(...)],
        price: Annotated[Decimal, Form(...)],
        stock: Annotated[int, Form(...)],
        category_id: Annotated[int, Form(...)],
        description: Annotated[str | None, Form()] = None,
    ) -> 'ProductCreateRequestSchema':
        return cls(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category_id=category_id,
        )


class ProductResponseSchema(BaseModel):
    """
    Модель для ответа с данными товара.
    Используется в GET-запросах.
    """

    id: int = Field(description='Уникальный идентификатор товара')
    name: str = Field(description='Название товара')
    description: str | None = Field(
        default=None, description='Описание товара'
    )
    price: float = Field(description='Цена товара')
    image_url: str | None = Field(
        default=None, description='URL изображения товара'
    )
    stock: int = Field(description='Количество товара на складе')
    category_id: int = Field(description='ID категории')
    seller_id: int = Field(description='ID продавца')
    rating: float = Field(default=0.0, description='Рейтинг товара')
    is_active: bool = Field(
        default=True, description='Активность товара (показывается или нет)'
    )

    model_config = ConfigDict(from_attributes=True)


class ProductListResponseSchema(BaseModel):
    """
    Список пагинации для товаров.
    """

    items: list[ProductResponseSchema] = Field(
        description='Товары для текущей страницы'
    )
    total: int = Field(ge=0, description='Общее количество товаров')
    page: int = Field(ge=1, description='Номер текущей страницы')
    page_size: int = Field(ge=1, description='Количество товаров на странице')

    model_config = ConfigDict(from_attributes=True)
