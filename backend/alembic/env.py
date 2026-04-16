import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from backend.models.base import Base
from backend.models.user import User        # noqa
from backend.models.token import TokenBalance, TokenTransaction  # noqa
from backend.models.generation import Generation  # noqa
from backend.core.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


run_migrations_online()
