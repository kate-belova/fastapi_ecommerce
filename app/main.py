from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import uvicorn
from fastapi import FastAPI
from loguru import logger
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from app.routers import routers

app = FastAPI(title='FastAPI Интернет-магазин')

BASE_DIR = Path(__file__).parent.parent
MEDIA_DIR = BASE_DIR / 'media'
MEDIA_DIR.mkdir(exist_ok=True)

app.mount('/media', StaticFiles(directory=str(MEDIA_DIR)), name='media')

logger.add(
    'info.log',
    format='Log: [{extra[log_id]}:{time} - {level} - {message}]',
    level='INFO',
    rotation='10 MB',
    retention='30 days',
    enqueue=True,
)


@app.middleware('http')
async def log_middleware(request: Request, call_next):
    log_id = str(uuid4())
    with logger.contextualize(log_id=log_id):
        try:
            response = await call_next(request)
            if response.status_code in [401, 402, 403, 404]:
                logger.warning(f'Request to {request.url.path} failed')
            else:
                logger.info('Successfully accessed ' + request.url.path)
        except Exception as ex:
            logger.error(f'Request to {request.url.path} failed: {ex}')
            response = JSONResponse(
                content={'success': False, 'error': 'Internal server error'},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return response


for router in routers:
    app.include_router(router)


@app.get('/health', summary='Проверить работоспособность сервиса')
async def health_check() -> dict[str, str]:
    """
    Проверка работоспособности сервиса.
    """

    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'FastAPI Ecommerce',
    }


@app.get('/', summary='Получить приветствие')
async def root() -> dict:
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    return {'message': 'Добро пожаловать в API интернет-магазина!'}


if __name__ == '__main__':
    uvicorn.run('app.main:app', reload=True)
