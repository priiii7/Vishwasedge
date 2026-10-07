"""Async SQLAlchemy engine/session + seed default user."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.security import hash_password
from backend.db.models import Base, User

logger = get_logger(__name__)

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.username == settings.default_admin_username))
        if result.scalar_one_or_none() is None:
            session.add(
                User(
                    username=settings.default_admin_username,
                    hashed_password=hash_password(settings.default_admin_password),
                    role="admin",
                )
            )
            await session.commit()
            logger.info("seeded_default_user", username=settings.default_admin_username)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
