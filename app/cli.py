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
def create_test_users():
    """Create test sellers and buyers"""

    async def _create_test_users():
        async with async_session_maker() as session:
            test_users = [
                {
                    'email': 'tech.seller@example.com',
                    'password': 'seller123',
                    'role': 'seller',
                    'description': 'Продавец электроники',
                },
                {
                    'email': 'book.store@example.com',
                    'password': 'seller123',
                    'role': 'seller',
                    'description': 'Книжный магазин',
                },
                {
                    'email': 'buyer1@example.com',
                    'password': 'buyer123',
                    'role': 'buyer',
                    'description': 'Тестовый покупатель 1',
                },
                {
                    'email': 'buyer2@example.com',
                    'password': 'buyer123',
                    'role': 'buyer',
                    'description': 'Тестовый покупатель 2',
                },
            ]

            created_count = 0
            for user_data in test_users:
                existing_user = await session.scalar(
                    select(UserModel).where(
                        UserModel.email == user_data['email']
                    )
                )

                if not existing_user:
                    user = UserModel(
                        email=user_data['email'],
                        hashed_password=hash_password(user_data['password']),
                        role=user_data['role'],
                        is_active=True,
                    )
                    session.add(user)
                    created_count += 1
                    click.echo(
                        f"✅ Created {user_data['role']}: {user_data['email']}"
                    )

            await session.commit()
            click.echo(f'🎉 Created {created_count} test users!')

    asyncio.run(_create_test_users())


@cli.command()
def list_users():
    """List all users with their roles"""

    async def _list_users():
        async with async_session_maker() as session:
            users = await session.scalars(select(UserModel))

            click.echo('👥 All users:')
            for user in users:
                role_icon = (
                    '👑'
                    if user.role == 'admin'
                    else '🛒' if user.role == 'seller' else '👤'
                )
                status = '✅ Active' if user.is_active else '❌ Inactive'
                click.echo(
                    f'  {role_icon} {user.email} ({user.role}) - {status}'
                )

    asyncio.run(_list_users())


@cli.command()
def populate_test_data():
    """Populate database with test categories, users and products"""

    async def _populate_test_data():
        from decimal import Decimal
        from sqlalchemy import select
        from app.models import CategoryModel, ProductModel, UserModel

        async with async_session_maker() as session:
            existing_categories = await session.scalar(select(CategoryModel))
            if existing_categories:
                click.echo(
                    'ℹ️ Database already contains data, skipping population'
                )
                return

            click.echo('📦 Creating test data...')

            parent_categories_data = [
                {'name': 'Электроника'},
                {'name': 'Книги'},
                {'name': 'Дом и быт'},
            ]

            parent_categories = {}
            for cat_data in parent_categories_data:
                category = CategoryModel(**cat_data)
                session.add(category)
                parent_categories[cat_data['name']] = category

            await session.flush()

            child_categories_data = [
                {
                    'name': 'Смартфоны',
                    'parent_id': parent_categories['Электроника'].id,
                },
                {
                    'name': 'Ноутбуки',
                    'parent_id': parent_categories['Электроника'].id,
                },
                {
                    'name': 'Планшеты',
                    'parent_id': parent_categories['Электроника'].id,
                },
                {
                    'name': 'Наушники',
                    'parent_id': parent_categories['Электроника'].id,
                },
                {
                    'name': 'Программирование',
                    'parent_id': parent_categories['Книги'].id,
                },
                {
                    'name': 'Художественная литература',
                    'parent_id': parent_categories['Книги'].id,
                },
                {
                    'name': 'Научпоп и образование',
                    'parent_id': parent_categories['Книги'].id,
                },
                {
                    'name': 'Бизнес и экономика',
                    'parent_id': parent_categories['Книги'].id,
                },
                {
                    'name': 'Техника для дома',
                    'parent_id': parent_categories['Дом и быт'].id,
                },
                {
                    'name': 'Мебель',
                    'parent_id': parent_categories['Дом и быт'].id,
                },
                {
                    'name': 'Кухонная утварь',
                    'parent_id': parent_categories['Дом и быт'].id,
                },
            ]

            categories = {}
            for cat_data in child_categories_data:
                category = CategoryModel(**cat_data)
                session.add(category)
                categories[cat_data['name']] = category

            await session.flush()

            tech_seller = UserModel(
                email='tech.seller@example.com',
                hashed_password=hash_password('seller123'),
                role='seller',
                is_active=True,
            )

            book_seller = UserModel(
                email='book.store@example.com',
                hashed_password=hash_password('seller123'),
                role='seller',
                is_active=True,
            )

            home_seller = UserModel(
                email='home.goods@example.com',
                hashed_password=hash_password('seller123'),
                role='seller',
                is_active=True,
            )

            session.add_all([tech_seller, book_seller, home_seller])
            await session.flush()

            electronics_products = [
                {
                    'name': 'iPhone 15 Pro 128GB',
                    'description': 'Флагманский смартфон Apple '
                    'с титановым корпусом и камерой 48 МП',
                    'price': Decimal('109999.00'),
                    'stock': 15,
                    'category_id': categories['Смартфоны'].id,
                    'seller_id': tech_seller.id,
                },
                {
                    'name': 'Samsung Galaxy S24 Ultra 256GB',
                    'description': 'Смартфон с AI-функциями '
                    'и стилусом S Pen, экран 6.8"',
                    'price': Decimal('89999.00'),
                    'stock': 12,
                    'category_id': categories['Смартфоны'].id,
                    'seller_id': tech_seller.id,
                },
                {
                    'name': 'Xiaomi Redmi Note 13 Pro 8/256GB',
                    'description': 'Смартфон с AMOLED экраном '
                    'и камерой 200 МП',
                    'price': Decimal('34999.00'),
                    'stock': 25,
                    'category_id': categories['Смартфоны'].id,
                    'seller_id': tech_seller.id,
                },
                {
                    'name': 'MacBook Air M3 13" 8/256GB',
                    'description': 'Ультрабук Apple на чипе M3, Retina дисплей',
                    'price': Decimal('129999.00'),
                    'stock': 8,
                    'category_id': categories['Ноутбуки'].id,
                    'seller_id': tech_seller.id,
                },
                {
                    'name': 'ASUS ROG Strix G16 Gaming Laptop',
                    'description': 'Игровой ноутбук с RTX 4060 '
                    'и процессором Intel Core i7',
                    'price': Decimal('149999.00'),
                    'stock': 5,
                    'category_id': categories['Ноутбуки'].id,
                    'seller_id': tech_seller.id,
                },
                {
                    'name': 'Apple AirPods Pro 2',
                    'description': 'Беспроводные наушники с шумоподавлением',
                    'price': Decimal('24999.00'),
                    'stock': 20,
                    'category_id': categories['Наушники'].id,
                    'seller_id': tech_seller.id,
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
                    'seller_id': book_seller.id,
                },
                {
                    'name': 'Python. К вершинам мастерства',
                    'description': 'Лучано Рамальо - углубленное руководство по Python',
                    'price': Decimal('2199.00'),
                    'stock': 25,
                    'category_id': categories['Программирование'].id,
                    'seller_id': book_seller.id,
                },
                {
                    'name': '1984',
                    'description': 'Джордж Оруэлл - классика антиутопии',
                    'price': Decimal('599.00'),
                    'stock': 50,
                    'category_id': categories['Художественная литература'].id,
                    'seller_id': book_seller.id,
                },
                {
                    'name': 'Три товарища',
                    'description': 'Эрих Мария Ремарк - роман о дружбе и любви',
                    'price': Decimal('799.00'),
                    'stock': 35,
                    'category_id': categories['Художественная литература'].id,
                    'seller_id': book_seller.id,
                },
                {
                    'name': 'Краткая история времени',
                    'description': 'Стивен Хокинг - '
                    'о природе пространства и времени',
                    'price': Decimal('1299.00'),
                    'stock': 28,
                    'category_id': categories['Научпоп и образование'].id,
                    'seller_id': book_seller.id,
                },
                {
                    'name': 'Sapiens. Краткая история человечества',
                    'description': 'Юваль Ной Харари - '
                    'бестселлер об эволюции человечества',
                    'price': Decimal('1599.00'),
                    'stock': 22,
                    'category_id': categories['Научпоп и образование'].id,
                    'seller_id': book_seller.id,
                },
            ]

            home_products = [
                {
                    'name': 'Dyson V15 Detect Absolute',
                    'description': 'Беспроводной пылесос с лазерной '
                    'подсветкой и HEPA фильтром',
                    'price': Decimal('59999.00'),
                    'stock': 10,
                    'category_id': categories['Техника для дома'].id,
                    'seller_id': home_seller.id,
                },
                {
                    'name': 'Xiaomi Robot Vacuum Mop 2 Pro',
                    'description': 'Робот-пылесос с функцией мытья полов',
                    'price': Decimal('29999.00'),
                    'stock': 8,
                    'category_id': categories['Техника для дома'].id,
                    'seller_id': home_seller.id,
                },
                {
                    'name': 'Компьютерный стол ErgoStand',
                    'description': 'Эргономичный стол с регулировкой высоты',
                    'price': Decimal('15999.00'),
                    'stock': 15,
                    'category_id': categories['Мебель'].id,
                    'seller_id': home_seller.id,
                },
            ]

            all_products = (
                electronics_products + books_products + home_products
            )
            for prod_data in all_products:
                product = ProductModel(**prod_data)
                session.add(product)

            await session.commit()
            click.echo(
                f'✅ Created {len(parent_categories_data)} parent categories'
            )
            click.echo(
                f'✅ Created {len(child_categories_data)} child categories'
            )
            click.echo(f'✅ Created 3 sellers')
            click.echo(f'✅ Created {len(all_products)} products')
            click.echo('📱 Tech Seller: 6 products (electronics)')
            click.echo('📚 Book Seller: 6 products (books)')
            click.echo('🏠 Home Seller: 3 products (home goods)')

    asyncio.run(_populate_test_data())


@cli.command()
def list_categories():
    """List all categories with hierarchy"""

    async def _list_categories():
        from app.models import CategoryModel

        async with async_session_maker() as session:
            from sqlalchemy import select

            parent_categories = await session.scalars(
                select(CategoryModel).where(CategoryModel.parent_id == None)
            )

            click.echo('🌳 Category hierarchy:')
            for parent in parent_categories:
                click.echo(f'📁 {parent.name}')

                child_categories = await session.scalars(
                    select(CategoryModel).where(
                        CategoryModel.parent_id == parent.id
                    )
                )

                for child in child_categories:
                    from app.models import ProductModel
                    from sqlalchemy import select, func

                    product_count = await session.scalar(
                        select(func.count(ProductModel.id)).where(
                            ProductModel.category_id == child.id
                        )
                    )
                    click.echo(
                        f'   └── 📂 {child.name} ({product_count} products)'
                    )

    asyncio.run(_list_categories())


if __name__ == '__main__':
    cli()
