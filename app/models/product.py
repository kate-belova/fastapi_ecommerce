from decimal import Decimal
from typing import TYPE_CHECKING

# fmt: off
from sqlalchemy import (String, Integer, Boolean,
    Numeric, ForeignKey, Float, Index
)
# fmt: on
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models import CategoryModel

if TYPE_CHECKING:
    from app.models import ReviewModel, UserModel


class ProductModel(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(200))
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey('categories.id'), nullable=False, index=True
    )
    seller_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False, index=True
    )
    rating: Mapped[float] = mapped_column(
        Float, default=0.0, server_default='0.0', nullable=False
    )

    __table_args__ = (
        Index('ix_products_category_active', 'category_id', 'is_active'),
        Index('ix_products_price_stock', 'price', 'stock'),
    )

    category: Mapped['CategoryModel'] = relationship(
        'CategoryModel', back_populates='products'
    )
    seller: Mapped['UserModel'] = relationship(
        'UserModel', back_populates='products'
    )
    reviews: Mapped[list['ReviewModel']] = relationship(
        'ReviewModel', cascade='all, delete-orphan', back_populates='product'
    )
