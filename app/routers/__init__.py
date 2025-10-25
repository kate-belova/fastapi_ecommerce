from app.routers.categories import categories_router
from app.routers.products import products_router
from app.routers.reviews import reviews_router
from app.routers.users import users_router

routers = [categories_router, products_router, users_router, reviews_router]
