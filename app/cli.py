import asyncio
import os

import click
from sqlalchemy import select

from app.core.security import hash_password
from app.database.connection import async_session_maker
from app.models import UserModel


@click.group()
def cli():
    """User management CLI"""
    pass


@cli.command()
@click.option(
    '--email',
    default=lambda: os.getenv('ADMIN_EMAIL', 'admin@example.com'),
    help='Admin email (default: from ADMIN_EMAIL env)',
)
@click.option(
    '--password',
    default=lambda: os.getenv('ADMIN_PASSWORD'),
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help='Admin password (default: from ADMIN_PASSWORD env)',
)
def create_admin(email, password):
    """Create admin user from environment variables or interactively"""

    async def _create_admin():
        async with async_session_maker() as session:
            existing_user = await session.scalar(
                select(UserModel).where(UserModel.email == email)
            )

            if existing_user:
                click.echo(f'❌ User {email} already exists!')
                return

            admin_user = UserModel(
                email=email,
                hashed_password=hash_password(password),
                role='admin',
                is_active=True,
            )

            session.add(admin_user)
            await session.commit()
            click.echo(f'✅ Admin user {email} created successfully!')

    asyncio.run(_create_admin())


@cli.command()
def create_default_admin():
    """Create default admin from environment variables (non-interactive)"""

    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD')

    if not email or not password:
        click.echo(
            '❌ ADMIN_EMAIL and ADMIN_PASSWORD must be set in environment'
        )
        return

    async def _create_default_admin():
        async with async_session_maker() as session:
            existing_user = await session.scalar(
                select(UserModel).where(UserModel.email == email)
            )

            if existing_user:
                click.echo(f'ℹ️ Admin user {email} already exists')
                return

            admin_user = UserModel(
                email=email,
                hashed_password=hash_password(password),
                role='admin',
                is_active=True,
            )

            session.add(admin_user)
            await session.commit()
            click.echo(f'✅ Default admin user {email} created successfully!')

    asyncio.run(_create_default_admin())


@cli.command()
def list_admins():
    """List all admin users"""

    async def _list_admins():
        async with async_session_maker() as session:
            admins = await session.scalars(
                select(UserModel).where(UserModel.role == 'admin')
            )

            admin_list = list(admins)
            if not admin_list:
                click.echo('❌ No admin users found')
                return

            click.echo('👑 Admin users:')
            for admin in admin_list:
                status = '✅ Active' if admin.is_active else '❌ Inactive'
                click.echo(f'  - {admin.email} ({status})')

    asyncio.run(_list_admins())


@cli.command()
@click.option('--email', prompt='Email', help='User email to promote to admin')
def promote_to_admin(email):
    """Promote existing user to admin"""

    async def _promote_to_admin():
        async with async_session_maker() as session:
            user = await session.scalar(
                select(UserModel).where(UserModel.email == email)
            )

            if not user:
                click.echo(f'❌ User {email} not found!')
                return

            if user.role == 'admin':
                click.echo(f'ℹ️ User {email} is already an admin')
                return

            user.role = 'admin'
            await session.commit()
            click.echo(f'✅ User {email} promoted to admin successfully!')

    asyncio.run(_promote_to_admin())


@cli.command()
def populate_test_data():
    """Populate database with test categories and products"""

    async def _populate_test_data():
        from decimal import Decimal
        from sqlalchemy import select
        from app.models import CategoryModel, ProductModel

        async with async_session_maker() as session:
            existing_categories = await session.scalar(select(CategoryModel))
            if existing_categories:
                click.echo(
                    'ℹ️ Database already contains data, skipping population'
                )
                return

            admin = await session.scalar(
                select(UserModel).where(UserModel.role == 'admin')
            )
            if not admin:
                click.echo('❌ No admin user found! Create admin first.')
                return

            click.echo('📦 Creating test data...')

            categories_data = [
                {'name': 'Смартфоны и гаджеты'},
                {'name': 'Ноутбуки и компьютеры'},
                {'name': 'Техника для дома'},
                {'name': 'Программирование'},
                {'name': 'Художественная литература'},
                {'name': 'Научпоп и образование'},
            ]

            categories = {}
            for cat_data in categories_data:
                category = CategoryModel(**cat_data)
                session.add(category)
                categories[cat_data['name']] = category

            await session.flush()

            electronics_products = [
                {
                    'name': 'iPhone 15 Pro 128GB',
                    'description': 'Флагманский смартфон Apple с титановым '
                    'корпусом и камерой 48 МП',
                    'price': Decimal('109999.00'),
                    'stock': 15,
                    'category_id': categories['Смартфоны и гаджеты'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'Samsung Galaxy S24 Ultra 256GB',
                    'description': 'Смартфон с AI-функциями и стилусом S Pen, '
                    'экран 6.8"',
                    'price': Decimal('89999.00'),
                    'stock': 12,
                    'category_id': categories['Смартфоны и гаджеты'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'Xiaomi Redmi Note 13 Pro 8/256GB',
                    'description': 'Смартфон с AMOLED экраном '
                    'и камерой 200 МП',
                    'price': Decimal('34999.00'),
                    'stock': 25,
                    'category_id': categories['Смартфоны и гаджеты'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'MacBook Air M3 13" 8/256GB',
                    'description': 'Ультрабук Apple на чипе M3, '
                    'Retina дисплей',
                    'price': Decimal('129999.00'),
                    'stock': 8,
                    'category_id': categories['Ноутбуки и компьютеры'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'ASUS ROG Strix G16 Gaming Laptop',
                    'description': 'Игровой ноутбук с RTX 4060 и '
                    'процессором Intel Core i7',
                    'price': Decimal('149999.00'),
                    'stock': 5,
                    'category_id': categories['Ноутбуки и компьютеры'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'Dyson V15 Detect Absolute',
                    'description': 'Беспроводной пылесос '
                    'с лазерной подсветкой и HEPA фильтром',
                    'price': Decimal('59999.00'),
                    'stock': 10,
                    'category_id': categories['Техника для дома'].id,
                    'seller_id': admin.id,
                },
            ]

            books_products = [
                {
                    'name': 'Чистый код. Создание, анализ и рефакторинг',
                    'description': 'Роберт Мартин - '
                    'классика для программистов '
                    'о написании качественного кода',
                    'price': Decimal('1899.00'),
                    'stock': 30,
                    'category_id': categories['Программирование'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'Совершенный код. Мастер-класс',
                    'description': 'Стив Макконнелл - полное '
                    'руководство по разработке ПО',
                    'price': Decimal('2499.00'),
                    'stock': 20,
                    'category_id': categories['Программирование'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'Python. К вершинам мастерства',
                    'description': 'Лучано Рамальо - '
                    'углубленное руководство по Python',
                    'price': Decimal('2199.00'),
                    'stock': 25,
                    'category_id': categories['Программирование'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': '1984',
                    'description': 'Джордж Оруэлл - классика антиутопии',
                    'price': Decimal('599.00'),
                    'stock': 50,
                    'category_id': categories['Художественная литература'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'Три товарища',
                    'description': 'Эрих Мария Ремарк - '
                    'роман о дружбе и любви',
                    'price': Decimal('799.00'),
                    'stock': 35,
                    'category_id': categories['Художественная литература'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'Краткая история времени',
                    'description': 'Стивен Хокинг - '
                    'о природе пространства и времени',
                    'price': Decimal('1299.00'),
                    'stock': 28,
                    'category_id': categories['Научпоп и образование'].id,
                    'seller_id': admin.id,
                },
                {
                    'name': 'Sapiens. Краткая история человечества',
                    'description': 'Юваль Ной Харари - '
                    'бестселлер об эволюции человечества',
                    'price': Decimal('1599.00'),
                    'stock': 22,
                    'category_id': categories['Научпоп и образование'].id,
                    'seller_id': admin.id,
                },
            ]

            all_products = electronics_products + books_products
            for prod_data in all_products:
                product = ProductModel(**prod_data)
                session.add(product)

            await session.commit()
            click.echo(
                f'✅ Created {len(categories_data)} categories '
                f'and {len(all_products)} products!'
            )
            click.echo('📱 Electronics: 6 products')
            click.echo('📚 Books: 7 products')

    asyncio.run(_populate_test_data())


if __name__ == '__main__':
    cli()
