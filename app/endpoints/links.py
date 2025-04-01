from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone
from app import schemas, crud
from app.database import SessionLocal
from app.endpoints.auth import get_current_user, get_current_user_optional
from app.schemas import UserResponse

from app.utils.cache import cache_link, get_cached_link, invalidate_cached_link

router = APIRouter()

async def get_db():
    async with SessionLocal() as db:
        yield db

@router.post("/shorten", response_model=schemas.LinkResponse)
async def create_short_link(
    link: schemas.LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_optional)
):
    """
    Создаем короткую ссылку. Если пользователь авторизован — привязываем к его owner_id
    """
    owner_id = current_user.id if current_user else None
    db_link = await crud.create_link(db, link, owner_id=owner_id)

    await cache_link(db_link.short_code, {"original_url": db_link.original_url})
    return db_link

@router.get("/search", response_model=List[schemas.LinkResponse])
async def search_links(original_url: str, db: AsyncSession = Depends(get_db)):
    """
    Ищем все короткие ссылки по оригинальному URL
    """
    links = await crud.search_link_by_original_url(db, original_url)
    if not links:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ссылки не найдены"
        )
    return links

@router.get("/{short_code}/stats", response_model=schemas.LinkStats)
async def get_link_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    """
    Возвращаем статистику по короткой ссылке
    """
    db_link = await crud.get_link_by_short_code(db, short_code)
    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ссылка не найдена"
        )
    return db_link

@router.get("/{short_code}")
async def redirect_to_original(
    short_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Отправляем на оригинальный URL по короткому коду
    """
    cached = await get_cached_link(short_code)
    if cached:
        db_link = await crud.get_link_by_short_code(db, short_code)
        if not db_link:
            raise HTTPException(status_code=404, detail="Ссылка не найдена")
        if db_link.expires_at and db_link.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Срок действия ссылки истёк")

        await crud.increment_redirect_count(db, db_link)
        return RedirectResponse(url=cached["original_url"])

    db_link = await crud.get_link_by_short_code(db, short_code)
    if not db_link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    if db_link.expires_at and db_link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Срок действия ссылки истёк")

    await crud.increment_redirect_count(db, db_link)
    await cache_link(short_code, {"original_url": db_link.original_url})
    return RedirectResponse(url=db_link.original_url)

@router.delete("/{short_code}", response_model=schemas.LinkResponse)
async def delete_short_link(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Удаляем короткую ссылку, доступно только создателю ссылки
    """
    db_link = await crud.get_link_by_short_code(db, short_code)
    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ссылка не найдена"
        )
    if db_link.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на удаление этой ссылки"
        )

    deleted_link = await crud.delete_link(db, short_code)
    await invalidate_cached_link(short_code)
    return deleted_link

@router.put("/{short_code}", response_model=schemas.LinkResponse)
async def update_short_link(
    short_code: str,
    link_update: schemas.LinkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Обновляем оригинальный URL и/или expires_at, доступно только создателю ссылки
    """
    db_link = await crud.get_link_by_short_code(db, short_code)
    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ссылка не найдена"
        )
    if db_link.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на изменение этой ссылки"
        )

    updated_link = await crud.update_link(db, short_code, link_update)
    await invalidate_cached_link(short_code)
    await cache_link(short_code, {"original_url": updated_link.original_url})
    return updated_link
