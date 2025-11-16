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


if __name__ == '__main__':
    cli()
