import json
import aioredis
from app.config import settings

async def cache_link(short_code: str, link_data: dict, expire: int = 3600):
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as redis:
        await redis.setex(short_code, expire, json.dumps(link_data))

async def get_cached_link(short_code: str):
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as redis:
        data = await redis.get(short_code)
    if data:
        return json.loads(data)
    return None

async def invalidate_cached_link(short_code: str):
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as redis:
        await redis.delete(short_code)
