import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app
from app.initial_db import init_db
import runpy
from unittest.mock import patch

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Добро пожаловать в Shorturler!"

@pytest.mark.asyncio
async def test_init_db():
    try:
        await init_db()
    except Exception as e:
        pytest.fail(f"init_db() вызвал исключение: {e}")

def test_uvicorn_run_called():
    with patch("uvicorn.run") as mock_run:
        runpy.run_module("app.main", run_name="__main__")
        mock_run.assert_called_once()
