from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.core.security import get_current_user
from app.database.depends import get_async_db
from app.models import OrderModel, OrderItemModel, UserModel, CartItemModel
from app.routers.cart import clear_user_cart
from app.schemas import OrderResponseSchema
from app.schemas.order import OrderListResponseSchema

orders_router = APIRouter(prefix='/orders', tags=['orders'])


async def _load_order_with_items(
    db: AsyncSession, order_id: int
) -> OrderModel | None:
    get_order_stmt = (
        select(OrderModel)
        .options(
            selectinload(OrderModel.items).selectinload(
                OrderItemModel.product
            ),
        )
        .where(OrderModel.id == order_id)
    )
    result = await db.scalars(get_order_stmt)
    order = result.first()
    return order


@orders_router.post(
    '/checkout',
    summary='Создать заказ на основе корзины пользователя',
    response_model=OrderResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def checkout_order(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> OrderModel | None:
    """
    Создаёт заказ на основе текущей корзины пользователя.
    Сохраняет позиции заказа, вычитает остатки и очищает корзину.
    """
    get_cart_item_stmt = (
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(CartItemModel.user_id == current_user.id)
        .order_by(CartItemModel.id)
    )
    cart_result = await db.scalars(get_cart_item_stmt)
    cart_items = cart_result.all()
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Cart is empty'
        )

    order = OrderModel(user_id=current_user.id)
    total_amount = Decimal('0')

    for cart_item in cart_items:
        product = cart_item.product
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Product {cart_item.product_id} is unavailable',
            )
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Not enough items of product {product.name} in stock',
            )

        unit_price = product.price
        if unit_price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Product {product.name} price is not set',
            )
        total_price = unit_price * cart_item.quantity
        total_amount += total_price

        order_item = OrderItemModel(
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            unit_price=unit_price,
            total_price=total_price,
        )
        order.items.append(order_item)

        product.stock -= cart_item.quantity

    order.total_amount = total_amount
    db.add(order)

    await clear_user_cart(db, current_user.id)
    await db.commit()

    created_order = await _load_order_with_items(db, order.id)
    if not created_order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to load created order',
        )
    return created_order


@orders_router.get(
    '/',
    summary='Получить список заказов пользователя',
    response_model=OrderListResponseSchema,
)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> OrderListResponseSchema:
    """
    Возвращает заказы текущего пользователя с простой пагинацией.
    """
    get_orders_number_stmt = select(func.count(OrderModel.id)).where(
        OrderModel.user_id == current_user.id
    )
    total = await db.scalar(get_orders_number_stmt)

    get_orders_stmt = (
        select(OrderModel)
        .options(
            selectinload(OrderModel.items).selectinload(OrderItemModel.product)
        )
        .where(OrderModel.user_id == current_user.id)
        .order_by(OrderModel.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.scalars(get_orders_stmt)
    orders = result.all()

    order_schemas = [
        OrderResponseSchema.model_validate(order) for order in orders
    ]

    return OrderListResponseSchema(
        items=order_schemas, total=total or 0, page=page, page_size=page_size
    )


@orders_router.get(
    '/{order_id}',
    summary='Получить информацию о заказе по его id',
    response_model=OrderResponseSchema,
)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> OrderModel | None:
    """
    Возвращает детальную информацию по заказу,
    если он принадлежит текущему пользователю.
    """

    order = await _load_order_with_items(db, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Order not found'
        )
    return order
