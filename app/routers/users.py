import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import SECRET_KEY, ALGORITHM
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.database.depends import get_async_db
from app.models import UserModel
from app.schemas import UserResponseSchema, UserCreateRequestSchema

users_router = APIRouter(prefix='/users', tags=['users'])


@users_router.post(
    '/',
    summary='Зарегистрировать нового пользователя в системе',
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponseSchema,
)
async def create_user(
    user: UserCreateRequestSchema, db: AsyncSession = Depends(get_async_db)
) -> UserModel | None:
    """
    Регистрирует нового пользователя с ролью 'buyer' или 'seller'.
    """
    get_user_stmt = select(UserModel).where(UserModel.email == user.email)
    result = await db.execute(get_user_stmt)
    existing_user = result.first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Email already registered',
        )

    new_user = UserModel(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@users_router.post('/token', summary='Получить аутентификационные токены')
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, dict | str] | None:
    """
    Аутентифицирует пользователя и возвращает access_token и refresh_token.
    """
    get_user_stmt = select(UserModel).where(
        UserModel.email == form_data.username
    )
    result = await db.scalars(get_user_stmt)
    user = result.first()
    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    access_token = create_access_token(
        data={'sub': user.email, 'role': user.role, 'id': user.id}
    )
    refresh_token = create_refresh_token(
        data={'sub': user.email, 'role': user.role, 'id': user.id}
    )
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer',
    }


@users_router.post(
    '/refresh-token', summary='Обновление access token с помощью refresh token'
)
async def get_refresh_token(
    refresh_token: str, db: AsyncSession = Depends(get_async_db)
):
    """
    Обновляет access_token с помощью refresh_token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate refresh token',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    get_user_stmt = select(UserModel).where(
        UserModel.email == email, UserModel.is_active == True
    )
    result = await db.scalars(get_user_stmt)
    user = result.first()
    if user is None:
        raise credentials_exception

    access_token = create_access_token(
        data={'sub': user.email, 'role': user.role, 'id': user.id}
    )
    return {'access_token': access_token, 'token_type': 'bearer'}
