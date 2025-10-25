import uvicorn
from fastapi import FastAPI

from app.routers import routers

app = FastAPI(title='FastAPI Интернет-магазин')

for router in routers:
    app.include_router(router)


@app.get('/', summary='Получить приветствие')
async def root() -> dict:
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    return {'message': 'Добро пожаловать в API интернет-магазина!'}


if __name__ == '__main__':
    uvicorn.run('app.main:app', reload=True)
