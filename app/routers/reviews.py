from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.security import get_current_user
from app.database.depends import get_async_db
from app.models import ReviewModel, UserModel, ProductModel
from app.schemas import ReviewResponseSchema, ReviewCreateRequestSchema

reviews_router = APIRouter(prefix='/reviews', tags=['reviews'])


@reviews_router.get(
    '/',
    summary='Получить список всех активных отзывов',
    response_model=list[ReviewResponseSchema],
)
async def get_reviews(
    db: AsyncSession = Depends(get_async_db),
) -> Sequence[ReviewModel]:
    """
    Возвращает список всех активных отзывов.
    """
    get_reviews_stmt = select(ReviewModel).where(ReviewModel.is_active == True)
    result = await db.scalars(get_reviews_stmt)
    reviews = result.all()
    return reviews


@reviews_router.get(
    '/products/{product_id}/reviews',
    summary='Получить активные отзывы об активном товаре по его id',
    response_model=list[ReviewResponseSchema],
)
async def get_product_reviews(
    product_id: int, db: AsyncSession = Depends(get_async_db)
) -> Sequence[ReviewModel]:
    """
    Возвращает список всех активных отзывов на активный товар.
    """
    get_product_stmt = select(ProductModel).where(
        ProductModel.id == product_id, ProductModel.is_active == True
    )
    result = await db.scalars(get_product_stmt)
    product = result.first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive',
        )

    get_reviews_stmt = select(ReviewModel).where(
        ReviewModel.product_id == product_id, ReviewModel.is_active == True
    )
    result = await db.scalars(get_reviews_stmt)
    reviews = result.all()
    return reviews


async def update_product_rating(product_id: int, db: AsyncSession) -> None:
    """
    Обновляет средний рейтинг активного товара по его ID.
    """
    get_avg_product_grade_stmt = select(func.avg(ReviewModel.grade)).where(
        ReviewModel.product_id == product_id, ReviewModel.is_active == True
    )
    result = await db.execute(get_avg_product_grade_stmt)
    avg_rating = result.scalar() or 0.0

    product = await db.get(ProductModel, product_id)
    product.rating = float(avg_rating)
    await db.commit()


@reviews_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    summary='Написать новый отзыв на активный товар',
    response_model=ReviewResponseSchema,
)
async def create_review(
    review: ReviewCreateRequestSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> ReviewModel | None:
    """
    Создаёт новый отзыв для активного товара, привязанный
    к текущему покупателю (только для 'buyer').
    """
    if current_user.role != 'buyer':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Оставлять отзывы могут только покупатели',
        )

    get_product_stmt = select(ProductModel).where(
        ProductModel.id == review.product_id,
        ProductModel.is_active == True,
    )
    result = await db.scalars(get_product_stmt)
    product = result.first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive',
        )

    existing_review_stmt = select(ReviewModel).where(
        ReviewModel.user_id == current_user.id,
        ReviewModel.product_id == review.product_id,
        ReviewModel.is_active == True,
    )
    existing_review = await db.scalar(existing_review_stmt)
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Вы уже оставляли отзыв на этот товар',
        )

    if not (1 <= review.grade <= 5):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='Grade should be from 1 to 5',
        )

    new_review = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(new_review)
    await db.commit()
    await update_product_rating(product_id=product.id, db=db)

    await db.refresh(new_review)
    return new_review


@reviews_router.delete(
    '/{review_id}',
    summary='Логически удалить (сделать неактивным) отзыв по его id',
)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> dict[str, str] | None:
    """
    Логически удаляет отзыв по его ID, устанавливая is_active=False.
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Удалять отзывы может только администратор',
        )

    get_review_stmt = select(ReviewModel).where(
        ReviewModel.id == review_id,
        ReviewModel.is_active == True,
    )
    result = await db.scalars(get_review_stmt)
    review = result.first()
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Review not found or inactive',
        )

    review.is_active = False
    await db.commit()
    await update_product_rating(product_id=review.product_id, db=db)

    return {'status': 'success', 'message': 'Review marked as inactive'}
