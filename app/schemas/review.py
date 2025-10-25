from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ReviewCreateRequestSchema(BaseModel):
    """
    Модель для создания отзыва.
    Используется в POST запросе.
    """

    product_id: int = Field(
        description='Идентификатор товара, на который пишется отзыв'
    )
    comment: str | None = Field(
        default=None, description='Комментарий о товаре'
    )
    grade: int = Field(ge=1, le=5, description='Оценка товара (от 1 до 5)')


class ReviewResponseSchema(BaseModel):
    """
    Модель для ответа с данными отзыва.
    Используется в GET-запросах.
    """

    id: int = Field(description='Уникальный идентификатор отзыва')
    user_id: int = Field(
        description='Идентификатор пользователя, написавшего отзыв'
    )
    product_id: int = Field(
        description='Идентификатор товара, на который написан отзыв'
    )
    comment: str | None = Field(
        default=None, description='Комментарий о товаре'
    )
    comment_date: datetime = Field(
        default_factory=datetime.now, description='Дата написания отзыва'
    )
    grade: int = Field(ge=1, le=5, description='Оценка (от 1 до 5)')
    is_active: bool = Field(
        default=True, description='Активность отзыва (показывается или нет)'
    )

    model_config = ConfigDict(from_attributes=True)
