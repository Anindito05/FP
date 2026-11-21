"""Alembic environment. DDL always uses DATABASE_URL_DIRECT."""
import asyncio
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from app.config import get_settings
from app.database import Base
import app.models  # register mappings

config=context.config
target_metadata=Base.metadata

def run_migrations_offline():
    url=get_settings().database_url_direct
    if not url: raise RuntimeError("DATABASE_URL_DIRECT is required")
    context.configure(url=url,target_metadata=target_metadata,literal_binds=True,dialect_opts={"paramstyle":"named"},compare_type=True)
    with context.begin_transaction(): context.run_migrations()

def _run_sync(connection):
    context.configure(connection=connection,target_metadata=target_metadata,compare_type=True)
    with context.begin_transaction(): context.run_migrations()

async def _run_async():
    section=config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"]=get_settings().database_url_direct
    if not section["sqlalchemy.url"]: raise RuntimeError("DATABASE_URL_DIRECT is required")
    connectable=async_engine_from_config(section,prefix="sqlalchemy.",poolclass=pool.NullPool)
    async with connectable.connect() as connection: await connection.run_sync(_run_sync)
    await connectable.dispose()

def run_migrations_online(): asyncio.run(_run_async())

if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
