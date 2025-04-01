from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import random
import string
import hashlib

from app import models, schemas

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user_by_username(db: AsyncSession, username: str):
    stmt = select(models.User).where(models.User.username == username)
    result = await db.execute(stmt)
    return result.scalars().first()

def generate_short_code(custom_alias: str = None) -> str:
    if custom_alias:
        return custom_alias
    prefix = "hse"
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return prefix + random_part

async def create_link(db: AsyncSession, link: schemas.LinkCreate, owner_id: int = None):
    short_code = generate_short_code(link.custom_alias)
    db_link = models.Link(
        original_url=link.original_url,
        short_code=short_code,
        expires_at=link.expires_at,
        owner_id=owner_id
    )
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link

async def get_link_by_short_code(db: AsyncSession, short_code: str):
    stmt = select(models.Link).where(models.Link.short_code == short_code)
    result = await db.execute(stmt)
    return result.scalars().first()

async def delete_link(db: AsyncSession, short_code: str):
    db_link = await get_link_by_short_code(db, short_code)
    if db_link:
        await db.delete(db_link)
        await db.commit()
        return db_link
    return None

async def update_link(db: AsyncSession, short_code: str, link_update: schemas.LinkUpdate):
    db_link = await get_link_by_short_code(db, short_code)
    if db_link:
        if link_update.original_url is not None:
            db_link.original_url = link_update.original_url
        if link_update.expires_at is not None:
            db_link.expires_at = link_update.expires_at
        await db.commit()
        await db.refresh(db_link)
    return db_link

async def increment_redirect_count(db: AsyncSession, db_link: models.Link):
    db_link.redirect_count += 1
    db_link.last_accessed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(db_link)
    return db_link

async def search_link_by_original_url(db: AsyncSession, original_url: str):
    stmt = select(models.Link).where(models.Link.original_url == original_url)
    result = await db.execute(stmt)
    return result.scalars().all()
