import asyncio
import time
import pytest
from httpx import AsyncClient

CONCURRENT_REQUESTS = 200
RESPONSE_TIME_THRESHOLD = 0.5

@pytest.mark.asyncio
async def test_load_redirect(async_client: AsyncClient):
    original_url = "https://example.com/loadtest"
    create_resp = await async_client.post(
        "/links/shorten", 
        json={"original_url": original_url}
    )
    assert create_resp.status_code == 200, f"Не удалось создать ссылку: {create_resp.text}"
    data = create_resp.json()
    short_code = data["short_code"]

    async def single_redirect_request():
        start = time.perf_counter()
        response = await async_client.get(f"/links/{short_code}", follow_redirects=False)
        elapsed = time.perf_counter() - start
        return response, elapsed

    tasks = [single_redirect_request() for _ in range(CONCURRENT_REQUESTS)]
    results = await asyncio.gather(*tasks)

    total_time = 0
    max_time = 0
    success_count = 0
    failure_count = 0

    for response, elapsed in results:
        total_time += elapsed
        if elapsed > max_time:
            max_time = elapsed
        if response.status_code in (302, 307):
            success_count += 1
        else:
            failure_count += 1

    avg_time = total_time / CONCURRENT_REQUESTS

    print(f"Load Test Results for GET /links/{{short_code}}:")
    print(f"  Total Requests: {CONCURRENT_REQUESTS}")
    print(f"  Successful responses: {success_count}")
    print(f"  Failed responses: {failure_count}")
    print(f"  Average response time: {avg_time:.4f} seconds")
    print(f"  Max response time: {max_time:.4f} seconds")

    assert failure_count == 0, "Некоторые запросы завершились ошибкой"
    assert avg_time < RESPONSE_TIME_THRESHOLD, f"Среднее время ответа слишком велико: {avg_time:.4f} секунд"
