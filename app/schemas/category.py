from pydantic import BaseModel, Field, ConfigDict


class CategoryCreateRequestSchema(BaseModel):
    """
    Модель для создания и обновления категории.
    Используется в POST и PUT запросах.
    """

    name: str = Field(
        min_length=3,
        max_length=50,
        description='Название категории (3-50 символов)',
    )
    parent_id: int | None = Field(
        default=None, description='ID родительской категории, если есть'
    )


class CategoryResponseSchema(BaseModel):
    """
    Модель для ответа с данными категории.
    Используется в GET-запросах.
    """

    id: int = Field(description='Уникальный идентификатор категории')
    name: str = Field(description='Название категории')
    parent_id: int | None = Field(
        default=None, description='ID родительской категории, если есть'
    )
    is_active: bool = Field(
        default=True, description='Активность категории (показывается или нет)'
    )

    model_config = ConfigDict(from_attributes=True)
