from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models import ProductModel, ReviewModel, CartItemModel, OrderModel


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String, default='buyer')

    products: Mapped[list['ProductModel']] = relationship(
        'ProductModel', back_populates='seller'
    )
    reviews: Mapped[list['ReviewModel']] = relationship(
        'ReviewModel', cascade='all, delete-orphan', back_populates='user'
    )
    cart_items: Mapped[list['CartItemModel']] = relationship(
        'CartItemModel', cascade='all, delete-orphan', back_populates='user'
    )
    orders: Mapped[list['OrderModel']] = relationship(
        'OrderModel', cascade='all, delete-orphan', back_populates='user'
    )

    CheckConstraint(
        "role IN ('buyer', 'seller', 'admin')", name='check_user_role'
    )
