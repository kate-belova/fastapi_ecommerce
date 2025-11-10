from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from starlette.responses import Response

from app.core.security import get_current_user
from app.database.depends import get_async_db
from app.models import ProductModel, CartItemModel, UserModel
from app.schemas import (
    CartResponseSchema,
    CartItemResponseSchema,
    CartItemCreateSchema,
    CartItemUpdateSchema,
)

cart_router = APIRouter(prefix='/cart', tags=['cart'])


async def _ensure_product_available(db: AsyncSession, product_id: int) -> None:
    get_product_stmt = select(ProductModel).where(
        ProductModel.id == product_id, ProductModel.is_active == True
    )
    result = await db.scalars(get_product_stmt)
    product = result.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive',
        )


async def _get_cart_item(
    db: AsyncSession, user_id: int, product_id: int
) -> CartItemModel | None:
    get_cart_item_stmt = (
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(
            CartItemModel.user_id == user_id,
            CartItemModel.product_id == product_id,
        )
    )
    result = await db.scalars(get_cart_item_stmt)
    cart_item = result.first()
    return cart_item


async def clear_user_cart(db: AsyncSession, user_id: int) -> None:
    """
    Сервисная функция для очистки корзины пользователя.
    Может использоваться как в эндпоинтах, так и в других сервисах.
    """
    clear_user_cart_stmt = delete(CartItemModel).where(
        CartItemModel.user_id == user_id
    )
    await db.execute(clear_user_cart_stmt)


@cart_router.get(
    '/',
    summary='Получить содержимое корзины',
    response_model=CartResponseSchema,
)
async def get_cart(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> CartResponseSchema:
    """
    Возвращает корзину текущего пользователя.
    Загружает все элементы CartItemModel и все товары из корзины пользователя
    одним асинхронным запросом с фильтрацией по user_id и сортировкой по id.
    """

    get_cart_items_stmt = (
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(CartItemModel.user_id == current_user.id)
        .order_by(CartItemModel.id)
    )
    result = await db.scalars(get_cart_items_stmt)
    cart_items = list(result.all())

    cart_item_schemas = [
        CartItemResponseSchema.model_validate(
            {
                'id': cart_item.id,
                'quantity': cart_item.quantity,
                'product': cart_item.product,
            }
        )
        for cart_item in cart_items
    ]

    total_quantity = sum(cart_item.quantity for cart_item in cart_items)

    price_items = (
        Decimal(cart_item.quantity) * cart_item.product.price
        for cart_item in cart_items
        if cart_item.product.price is not None
    )
    total_price_decimal = sum(price_items, Decimal('0'))

    return CartResponseSchema(
        user_id=current_user.id,
        items=cart_item_schemas,
        total_quantity=total_quantity,
        total_price=total_price_decimal,
    )


@cart_router.post(
    '/items',
    summary='Добавить товар в корзину',
    response_model=CartItemResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_item_to_cart(
    payload: CartItemCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> CartItemModel:
    """
    Добавляет товар в корзину пользователя или увеличивает его количество,
    если он уже есть.
    """
    await _ensure_product_available(db, payload.product_id)

    cart_item = await _get_cart_item(db, current_user.id, payload.product_id)
    if cart_item:
        cart_item.quantity += payload.quantity
    else:
        cart_item = CartItemModel(
            user_id=current_user.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        db.add(cart_item)

    await db.commit()
    updated_item = await _get_cart_item(
        db, current_user.id, payload.product_id
    )
    return updated_item


@cart_router.put(
    '/items/{product_id}',
    summary='Обновить количество товара в корзине',
    response_model=CartItemResponseSchema,
)
async def update_cart_item(
    product_id: int,
    payload: CartItemUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> CartItemModel:
    """
    Обновляет количество товара в корзине пользователя.
    """

    await _ensure_product_available(db, product_id)

    cart_item = await _get_cart_item(db, current_user.id, product_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail='Cart item not found')

    cart_item.quantity = payload.quantity
    await db.commit()
    updated_item = await _get_cart_item(db, current_user.id, product_id)
    return updated_item


@cart_router.delete(
    '/items/{product_id}',
    summary='Удалить товар из корзины',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_item_from_cart(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> Response:
    """
    Удаляет указанный товар из корзины пользователя.
    """

    cart_item = await _get_cart_item(db, current_user.id, product_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail='Cart item not found')

    await db.delete(cart_item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@cart_router.delete(
    '/',
    summary='Полностью очистить корзину',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_cart(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> Response:
    """
    Удаляются все записи CartItemModel, где user_id соответствует
    авторизованному пользователю, приславшему запрос.
    """
    await clear_user_cart(db, current_user.id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
