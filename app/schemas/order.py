from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from app.schemas import ProductResponseSchema


class OrderItemResponseSchema(BaseModel):
    id: int = Field(description='ID позиции заказа')
    product_id: int = Field(description='ID товара')
    quantity: int = Field(ge=1, description='Количество')
    unit_price: Decimal = Field(
        ge=0, description='Цена за единицу на момент покупки'
    )
    total_price: Decimal = Field(ge=0, description='Сумма по позиции')
    product: ProductResponseSchema | None = Field(
        default=None, description='Полная информация о товаре'
    )

    model_config = ConfigDict(from_attributes=True)


class OrderResponseSchema(BaseModel):
    id: int = Field(description='ID заказа')
    user_id: int = Field(description='ID пользователя')
    status: str = Field(description='Текущий статус заказа')
    total_amount: Decimal = Field(ge=0, description='Общая стоимость')
    created_at: datetime = Field(description='Время создания заказа')
    updated_at: datetime = Field(
        description='Время последнего обновления заказа'
    )
    items: list[OrderItemResponseSchema] = Field(
        default_factory=list, description='Список позиций'
    )

    model_config = ConfigDict(from_attributes=True)


class OrderListResponseSchema(BaseModel):
    items: list[OrderResponseSchema] = Field(
        description='Заказы на текущей странице'
    )
    total: int = Field(ge=0, description='Общее количество заказов')
    page: int = Field(ge=1, description='Текущая страница')
    page_size: int = Field(ge=1, description='Размер страницы')

    model_config = ConfigDict(from_attributes=True)
