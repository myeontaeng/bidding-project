from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    import app.models.announcement   # noqa: F401
    import app.models.filter_config  # noqa: F401
    import app.models.user           # noqa: F401
    import app.models.company        # noqa: F401
    import app.models.bid_application  # noqa: F401
    import app.models.award_record   # noqa: F401
    import app.models.document_template  # noqa: F401
    import app.models.audit_log      # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_announcements(conn)
        await _migrate_companies(conn)
        await _migrate_users(conn)


async def _migrate_announcements(conn):
    """기존 announcements 테이블에 누락된 컬럼 추가 (SQLite ALTER TABLE)."""
    result = await conn.execute(text("PRAGMA table_info(announcements)"))
    existing = {row[1] for row in result.fetchall()}
    new_cols = [
        ("ministry", "VARCHAR(200)"),
        ("support_type", "VARCHAR(100)"),
        ("budget_available", "FLOAT"),
        ("eligible_institutions", "JSON"),
        ("description", "TEXT"),
        ("opening_date", "DATETIME"),
    ]
    for col, col_type in new_cols:
        if col not in existing:
            await conn.execute(text(f"ALTER TABLE announcements ADD COLUMN {col} {col_type}"))


async def _migrate_companies(conn):
    result = await conn.execute(text("PRAGMA table_info(companies)"))
    existing = {row[1] for row in result.fetchall()}
    if "certifications" not in existing:
        await conn.execute(text("ALTER TABLE companies ADD COLUMN certifications JSON"))


async def _migrate_users(conn):
    result = await conn.execute(text("PRAGMA table_info(users)"))
    existing = {row[1] for row in result.fetchall()}
    if "role" not in existing:
        await conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'admin'"))
