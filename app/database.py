from collections.abc import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import settings


def _get_database_url() -> str:
    url = settings.DATABASE_URL
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Set it in Vercel Dashboard → Settings → Environment Variables."
        )

    # Convert postgres:// to postgresql+asyncpg://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    # Strip unsupported query parameters for asyncpg
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    unsupported = {"channel_binding", "pgbouncer", "connection_limit", "pool_timeout", "sslmode"}
    for key in unsupported:
        params.pop(key, None)
    new_query = urlencode(params, doseq=True)
    url = urlunparse(parsed._replace(query=new_query))

    return url


engine = None
async_session = None

try:
    _url = _get_database_url()
    engine = create_async_engine(_url, echo=False, future=True, connect_args={"ssl": "require"})
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
except Exception as e:
    import sys
    print(f"[DB INIT ERROR] {e}", file=sys.stderr)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session is None:
        raise RuntimeError(
            "Database is not configured. Set DATABASE_URL environment variable."
        )
    async with async_session() as session:
        yield session
