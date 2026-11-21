"""Async SQLAlchemy engine, session dependency and declarative Base."""
from collections.abc import AsyncIterator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings


class Base(DeclarativeBase):
    """Shared ORM metadata."""


def build_engine(database_url: str):
    """Create a pre-ping async engine. Incoming: database_url. Outgoing: AsyncEngine."""
    if not database_url:
        raise ValueError("DATABASE_URL must be configured")
    return create_async_engine(database_url, pool_pre_ping=True, pool_size=5, max_overflow=5)


_engine = None
_sessions = None


def _session_factory():
    global _engine, _sessions
    if _sessions is None:
        _engine = build_engine(get_settings().database_url)
        _sessions = async_sessionmaker(_engine, expire_on_commit=False)
    return _sessions


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped session. Incoming: none. Outgoing: AsyncIterator[AsyncSession]."""
    try:
        factory = _session_factory()
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database is not configured") from exc
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_health(session: AsyncSession) -> bool:
    """Probe database with SELECT 1. Incoming: session. Outgoing: bool."""
    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_engine() -> None:
    """Dispose cached engine during application shutdown."""
    global _engine, _sessions
    if _engine is not None:
        await _engine.dispose()
    _engine = _sessions = None
