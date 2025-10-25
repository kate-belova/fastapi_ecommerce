from datetime import datetime
from typing import TYPE_CHECKING

# fmt: off
from sqlalchemy import (ForeignKey, Text, DateTime,
    Integer, Boolean, CheckConstraint, Index
)
# fmt: on
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models import UserModel, ProductModel


class ReviewModel(Base):
    __tablename__ = 'reviews'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey('products.id'), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text)
    comment_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    grade: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped['UserModel'] = relationship(
        'UserModel', back_populates='reviews'
    )
    product: Mapped['ProductModel'] = relationship(
        'ProductModel', back_populates='reviews'
    )

    __table_args__ = (
        CheckConstraint(
            'grade >= 1 AND grade <= 5', name='check_reviews_grade_range'
        ),
        Index('ix_reviews_user_product', 'user_id', 'product_id', unique=True),
        Index('ix_reviews_product_grade', 'product_id', 'grade'),
    )
