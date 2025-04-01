import asyncio
import pytest_asyncio
import aioredis
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app
from app.endpoints.auth import get_db as auth_get_db
from app.endpoints.links import get_db as links_get_db
from app.config import settings

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
TestingSessionLocal = sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False
)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[auth_get_db] = override_get_db
app.dependency_overrides[links_get_db] = override_get_db

@pytest_asyncio.fixture(scope="session")
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="session")
async def async_client(prepare_database):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(autouse=True, scope="function")
async def clear_redis():
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as redis:
        await redis.flushdb()
    yield
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as redis:
        await redis.flushdb()
