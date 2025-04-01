import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import crud, models, schemas

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
TestingSessionLocal = sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest_asyncio.fixture(scope="module")
async def db() -> AsyncSession:
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_and_get_user(db: AsyncSession):
    user_data = schemas.UserCreate(username="crudtest", password="password")
    user = await crud.create_user(db, user_data)
    assert user.username == "crudtest"
    user_fetched = await crud.get_user_by_username(db, "crudtest")
    assert user_fetched.id == user.id

def test_generate_short_code_without_custom_alias():
    short_code = crud.generate_short_code()
    assert short_code.startswith("hse")
    assert len(short_code) == 9

def test_generate_short_code_with_custom_alias():
    custom_alias = "alias123"
    short_code = crud.generate_short_code(custom_alias)
    assert short_code == custom_alias

@pytest.mark.asyncio
async def test_create_link_and_get_by_short_code(db: AsyncSession):
    link_in = schemas.LinkCreate(original_url="https://www.hse.ru", expires_at=None, custom_alias=None)
    link = await crud.create_link(db, link_in, owner_id=1)
    assert link.original_url == "https://www.hse.ru"
    fetched = await crud.get_link_by_short_code(db, link.short_code)
    assert fetched.id == link.id

@pytest.mark.asyncio
async def test_delete_link(db: AsyncSession):
    link_in = schemas.LinkCreate(original_url="https://stepik.org", expires_at=None, custom_alias=None)
    link = await crud.create_link(db, link_in, owner_id=2)
    deleted = await crud.delete_link(db, link.short_code)
    assert deleted is not None
    not_found = await crud.get_link_by_short_code(db, link.short_code)
    assert not_found is None

@pytest.mark.asyncio
async def test_update_link(db: AsyncSession):
    link_in = schemas.LinkCreate(original_url="https://www.kaggle.com", expires_at=None, custom_alias="upd123")
    link = await crud.create_link(db, link_in, owner_id=3)
    new_url = "https://www.kaggle.com"
    new_expires = datetime.utcnow() + timedelta(days=1)
    update_data = schemas.LinkUpdate(original_url=new_url, expires_at=new_expires)
    updated = await crud.update_link(db, "upd123", update_data)
    assert updated.original_url == new_url
    assert abs((updated.expires_at - new_expires).total_seconds()) < 2

@pytest.mark.asyncio
async def test_increment_redirect_count(db: AsyncSession):
    link_in = schemas.LinkCreate(original_url="https://google.com", expires_at=None, custom_alias="inc123")
    link = await crud.create_link(db, link_in, owner_id=4)
    original_count = link.redirect_count
    updated_link = await crud.increment_redirect_count(db, link)
    assert updated_link.redirect_count == original_count + 1
    assert updated_link.last_accessed_at is not None
    now = datetime.utcnow()
    assert abs((now - updated_link.last_accessed_at).total_seconds()) < 5

@pytest.mark.asyncio
async def test_search_link_by_original_url(db: AsyncSession):
    url = "https://ya.ru"
    link_in = schemas.LinkCreate(original_url=url, expires_at=None, custom_alias="search123")
    link = await crud.create_link(db, link_in, owner_id=5)
    results = await crud.search_link_by_original_url(db, url)
    assert any(l.id == link.id for l in results)
