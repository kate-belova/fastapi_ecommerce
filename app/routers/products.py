from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.security import get_current_seller
from app.database.depends import get_async_db
from app.models import ProductModel, CategoryModel, UserModel
from app.schemas import (
    ProductResponseSchema,
    ProductCreateRequestSchema,
    ProductListResponseSchema,
)

products_router = APIRouter(prefix='/products', tags=['products'])


@products_router.get(
    '/',
    summary='Получить список всех активных товаров',
    response_model=ProductListResponseSchema,
)
async def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(
        None, description='ID категории для фильтрации'
    ),
    min_price: float | None = Query(
        None, ge=0, description='Минимальная цена товара'
    ),
    max_price: float | None = Query(
        None, ge=0, description='Максимальная цена товара'
    ),
    in_stock: bool | None = Query(
        None,
        description='true — только товары в наличии, false — только без остатка',
    ),
    seller_id: int | None = Query(
        None, description='ID продавца для фильтрации'
    ),
    db: AsyncSession = Depends(get_async_db),
) -> ProductListResponseSchema:
    """
    Возвращает список всех активных товаров.
    """
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='min_price не может быть больше max_price',
        )

    filters = [ProductModel.is_active == True]

    if category_id is not None:
        filters.append(ProductModel.category_id == category_id)
    if min_price is not None:
        filters.append(ProductModel.price >= min_price)
    if max_price is not None:
        filters.append(ProductModel.price <= max_price)
    if in_stock is not None:
        filters.append(
            ProductModel.stock > 0 if in_stock else ProductModel.stock == 0
        )
    if seller_id is not None:
        filters.append(ProductModel.seller_id == seller_id)

    total_stmt = select(func.count(ProductModel.id)).where(*filters)
    total = await db.scalar(total_stmt) or 0

    get_products_stmt = (
        select(ProductModel)
        .join(CategoryModel)
        .where(CategoryModel.is_active == True, *filters)
        .order_by(ProductModel.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.scalars(get_products_stmt)
    products = result.all()

    product_schemas = [
        ProductResponseSchema.model_validate(product) for product in products
    ]

    return ProductListResponseSchema(
        items=product_schemas, total=total, page=page, page_size=page_size
    )


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
