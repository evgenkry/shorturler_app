import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def register_user(client: AsyncClient, username: str, password: str):
    response = await client.post("/auth/register", json={"username": username, "password": password})
    return response

async def login_user(client: AsyncClient, username: str, password: str):
    response = await client.post("/auth/token", data={"username": username, "password": password})
    return response

async def create_short_link(client: AsyncClient, token: str, original_url: str, custom_alias: str = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {"original_url": original_url}
    if custom_alias:
        payload["custom_alias"] = custom_alias
    response = await client.post("/links/shorten", json=payload, headers=headers)
    return response

async def test_auth_and_links_flow(async_client: AsyncClient):
    username = "testuser"
    password = "testpass"
    
    response = await register_user(async_client, username, password)
    assert response.status_code == 200, f"Ошибка регистрации: {response.text}"
    user_data = response.json()
    assert "id" in user_data and user_data["username"] == username
    
    response_dup = await register_user(async_client, username, password)
    assert response_dup.status_code == 400, "Повторная регистрация не вернула ошибку 400"
    
    response = await login_user(async_client, username, password)
    assert response.status_code == 200, f"Ошибка авторизации: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data and token_data["token_type"] == "bearer"
    token = token_data["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/auth/me", headers=headers)
    assert response.status_code == 200, f"Ошибка получения /auth/me: {response.text}"
    user_me = response.json()
    assert user_me["username"] == username
    
    original_url = "https://example.com"
    response = await create_short_link(async_client, None, original_url)
    assert response.status_code == 200, f"Ошибка создания ссылки: {response.text}"
    link_data = response.json()
    short_code = link_data["short_code"]
    assert link_data["original_url"] == original_url
    
    original_url2 = "https://example.org"
    custom_alias = "customAlias123"
    response = await create_short_link(async_client, token, original_url2, custom_alias)
    assert response.status_code == 200, f"Ошибка создания ссылки с авторизацией: {response.text}"
    link_data_auth = response.json()
    assert link_data_auth["short_code"] == custom_alias
    
    response = await async_client.get("/links/search", params={"original_url": original_url})
    assert response.status_code == 200, f"Ошибка поиска ссылки: {response.text}"
    search_results = response.json()
    assert isinstance(search_results, list)
    assert any(link["original_url"] == original_url for link in search_results)
    
    response = await async_client.get(f"/links/{short_code}/stats")
    assert response.status_code == 200, f"Ошибка получения статистики ссылки: {response.text}"
    stats = response.json()
    assert stats["original_url"] == original_url
    assert "redirect_count" in stats
    
    response = await async_client.get(f"/links/{short_code}", follow_redirects=False)
    assert response.status_code in (302, 307), f"Редирект не выполнен: {response.text}"
    
    new_url = "https://updated.com"
    response = await async_client.put(f"/links/{custom_alias}", json={"original_url": new_url}, headers=headers)
    assert response.status_code == 200, f"Ошибка обновления ссылки: {response.text}"
    updated_link = response.json()
    assert updated_link["original_url"] == new_url
    
    response = await async_client.delete(f"/links/{custom_alias}", headers=headers)
    assert response.status_code == 200, f"Ошибка удаления ссылки: {response.text}"
    deleted_link = response.json()
    assert deleted_link["short_code"] == custom_alias
    
    response = await create_short_link(async_client, None, "https://noowner.com")
    assert response.status_code == 200, f"Ошибка создания ссылки: {response.text}"
    link_no_owner = response.json()
    response = await async_client.delete(f"/links/{link_no_owner['short_code']}", headers=headers)
    assert response.status_code == 403, "Удаление ссылки, не принадлежащей пользователю, должно вернуть 403"
