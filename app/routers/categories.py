from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.database.depends import get_async_db
from app.models import CategoryModel
from app.schemas import CategoryCreateRequestSchema, CategoryResponseSchema

categories_router = APIRouter(prefix='/categories', tags=['categories'])


@categories_router.get(
    '/',
    summary='Получить список всех активных категорий товаров',
    response_model=list[CategoryResponseSchema],
)
async def get_categories(
    db: AsyncSession = Depends(get_async_db),
) -> Sequence[CategoryModel]:
    """
    Возвращает список всех активных категорий товаров.
    """
    get_categories_stmt = select(CategoryModel).where(
        CategoryModel.is_active == True
    )
    result = await db.scalars(get_categories_stmt)
    categories = result.all()
    return categories


@categories_router.post(
    '/',
    summary='Создать новую категорию товаров',
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryResponseSchema,
)
async def create_category(
    category: CategoryCreateRequestSchema,
    db: AsyncSession = Depends(get_async_db),
) -> CategoryModel | None:
    """
    Создаёт новую категорию товаров.
    """
    if category.parent_id is not None:
        get_parent_stmt = select(CategoryModel).where(
            CategoryModel.id == category.parent_id,
            CategoryModel.is_active == True,
        )
        result = await db.scalars(get_parent_stmt)
        parent = result.first()

        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Category parent not found or inactive',
            )

    new_category = CategoryModel(**category.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category


@categories_router.put(
    '/{category_id}',
    summary='Полностью обновить (заменить) категорию по ее id',
    response_model=CategoryResponseSchema,
)
async def update_category(
    category_id: int,
    category_to_update: CategoryCreateRequestSchema,
    db: AsyncSession = Depends(get_async_db),
) -> CategoryModel | None:
    """
    Обновляет категорию по её ID.
    """
    get_category_stmt = select(CategoryModel).where(
        CategoryModel.id == category_id, CategoryModel.is_active == True
    )
    result = await db.scalars(get_category_stmt)
    category = result.first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found or inactive',
        )

    if category_to_update.parent_id is not None:
        get_parent_stmt = select(CategoryModel).where(
            CategoryModel.parent_id == category_to_update.parent_id,
            CategoryModel.is_active == True,
        )
        result = await db.scalars(get_parent_stmt)
        parent = result.first()

        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Category parent not found or inactive',
            )
        if parent.id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Category cannot be its own parent',
            )

    update_category_stmt = (
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(**category_to_update.model_dump(exclude_unset=True))
    )
    await db.execute(update_category_stmt)
    await db.commit()

    get_updated_category_stmt = select(CategoryModel).where(
        CategoryModel.id == category_id
    )
    result = await db.scalars(get_updated_category_stmt)
    updated_category = result.first()
    return updated_category


@categories_router.delete(
    '/{category_id}',
    summary='Логически удалить (сделать неактивной) категорию по ее id',
)
async def delete_category(
    category_id: int, db: AsyncSession = Depends(get_async_db)
) -> dict[str, str] | None:
    """
    Логически удаляет категорию по её ID, устанавливая is_active=False.
    """
    get_category_stmt = select(CategoryModel).where(
        CategoryModel.id == category_id, CategoryModel.is_active == True
    )
    result = await db.scalars(get_category_stmt)
    category = result.first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found or inactive',
        )

    category.is_active = False
    await db.commit()

    return {
        'status': 'success',
        'message': f'Category with ID {category_id} marked as inactive',
    }
