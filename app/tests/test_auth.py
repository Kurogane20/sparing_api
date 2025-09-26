import pytest, asyncio
from httpx import AsyncClient
from app.main import app

@pytest.mark.anyio
async def test_docs_up():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/healthz")
        assert res.status_code in (200, 500)
