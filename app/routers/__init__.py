from app.routers.cart import cart_router
from app.routers.categories import categories_router
from app.routers.orders import orders_router
from app.routers.products import products_router
from app.routers.reviews import reviews_router
from app.routers.users import users_router

# fmt: off
routers = [categories_router, products_router, users_router,
           reviews_router, cart_router, orders_router
]
# fmt: on
