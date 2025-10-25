from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models import ProductModel


class CategoryModel(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey('categories.id'), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index('ix_categories_parent_active', 'parent_id', 'is_active'),
    )

    products: Mapped[list['ProductModel']] = relationship(
        'ProductModel', back_populates='category'
    )

    parent: Mapped['CategoryModel | None'] = relationship(
        'CategoryModel',
        back_populates='children',
        remote_side='CategoryModel.id',
    )
    children: Mapped[list['CategoryModel']] = relationship(
        'CategoryModel', back_populates='parent'
    )
