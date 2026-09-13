import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.database import get_session
from app.deps import get_current_user
from app.main import app
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(session: AsyncSession) -> str:
    admin = User(
        name="Test Admin",
        email="admin@test.com",
        password_hash=hash_password("testpass"),
        role="admin",
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return create_access_token(subject=str(admin.id), role="admin", user_type="staff")


@pytest_asyncio.fixture
async def staff_token(session: AsyncSession) -> str:
    staff = User(
        name="Test Staff",
        email="staff@test.com",
        password_hash=hash_password("testpass"),
        role="staff",
    )
    session.add(staff)
    await session.commit()
    await session.refresh(staff)
    return create_access_token(subject=str(staff.id), role="staff", user_type="staff")


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
