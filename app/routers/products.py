from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.security import get_current_seller
from app.database.depends import get_async_db
from app.models import ProductModel, CategoryModel, UserModel
from app.schemas import ProductResponseSchema, ProductCreateRequestSchema

products_router = APIRouter(prefix='/products', tags=['products'])


@products_router.get(
    '/',
    summary='Получить список всех активных товаров',
    response_model=list[ProductResponseSchema],
)
async def get_products(
    db: AsyncSession = Depends(get_async_db),
) -> Sequence[ProductModel]:
    """
    Возвращает список всех активных товаров.
    """
    get_products_stmt = (
        select(ProductModel)
        .join(CategoryModel)
        .where(CategoryModel.is_active == True, ProductModel.is_active == True)
    )
    result = await db.scalars(get_products_stmt)
    products = result.all()
    return products


@products_router.post(
    '/',
    summary='Добавить новый товар',
    status_code=status.HTTP_201_CREATED,
    response_model=ProductResponseSchema,
)
async def create_product(
    product: ProductCreateRequestSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
) -> ProductModel | None:
    """
    Создаёт новый товар, привязанный к текущему продавцу (только для 'seller').
    """
    get_category_stmt = select(CategoryModel).where(
        CategoryModel.id == product.category_id,
        CategoryModel.is_active == True,
    )
    result = await db.scalars(get_category_stmt)
    category = result.first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Category not found or inactive',
        )

    new_product = ProductModel(
        **product.model_dump(), seller_id=current_user.id
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


@products_router.get(
    '/category/{category_id}',
    summary='Получить все активные товары определенной категории по ее id',
    response_model=list[ProductResponseSchema],
)
async def get_products_by_category(
    category_id: int, db: AsyncSession = Depends(get_async_db)
) -> Sequence[ProductModel] | None:
    """
    Возвращает список активных товаров в указанной активной категории по её ID.
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

    get_products_stmt = select(ProductModel).where(
        ProductModel.category_id == category_id, ProductModel.is_active == True
    )
    result = await db.scalars(get_products_stmt)
    products = result.all()
    return products


@products_router.get(
    '/{product_id}',
    summary='Получить информацию о товаре по его id',
    response_model=ProductResponseSchema,
)
async def get_product(
    product_id: int, db: AsyncSession = Depends(get_async_db)
) -> ProductModel | None:
    """
    Возвращает детальную информацию об активном товаре по его ID.
    """
    get_product_stmt = (
        select(ProductModel)
        .join(CategoryModel)
        .where(
            CategoryModel.is_active == True,
            ProductModel.id == product_id,
            ProductModel.is_active == True,
        )
    )
    result = await db.scalars(get_product_stmt)
    product = result.first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive',
        )
    return product


@products_router.put(
    '/{product_id}',
    summary='Полностью обновить (заменить) информацию о товаре по его id',
    response_model=ProductResponseSchema,
)
async def update_product(
    product_id: int,
    product_to_update: ProductCreateRequestSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
) -> ProductModel | None:
    """
    Обновляет товар по его ID.
    """
    get_product_stmt = (
        select(ProductModel)
        .join(CategoryModel)
        .where(
            CategoryModel.is_active == True,
            ProductModel.id == product_id,
            ProductModel.is_active == True,
        )
    )
    result = await db.scalars(get_product_stmt)
    product = result.first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive',
        )

    if product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only update your own products',
        )

    get_category_stmt = select(CategoryModel).where(
        CategoryModel.id == product_to_update.category_id,
        CategoryModel.is_active == True,
    )
    result = await db.scalars(get_category_stmt)
    category = result.first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Category not found or inactive',
        )

    update_product_stmt = (
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**product_to_update.model_dump())
    )
    await db.execute(update_product_stmt)
    await db.commit()
    await db.refresh(product)
    return product


@products_router.delete(
    '/{product_id}',
    summary='Логически удалить (сделать неактивным) товар по его id',
)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
) -> dict[str, str] | None:
    """
    Логически удаляет товар по его ID, устанавливая is_active = False.
    """
    get_product_stmt = (
        select(ProductModel)
        .join(CategoryModel)
        .where(
            CategoryModel.is_active == True,
            ProductModel.id == product_id,
            ProductModel.is_active == True,
        )
    )
    result = await db.scalars(get_product_stmt)
    product = result.first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive',
        )

    if product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only delete your own products',
        )

    product.is_active = False
    await db.commit()

    return {'status': 'success', 'message': 'Product marked as inactive'}
