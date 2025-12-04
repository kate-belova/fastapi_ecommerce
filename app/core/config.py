import os

from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('USER')}:{os.getenv('PASSWORD')}"
    f"@{os.getenv('HOST')}:{os.getenv('PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

if not SECRET_KEY:
    raise ValueError('SECRET_KEY must be set in environment variables')

if not DATABASE_URL:
    raise ValueError('DATABASE_URL must be set in environment variables')
