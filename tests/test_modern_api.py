# tests/test_modern_api.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_patient_modern(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/patients/",
        json={
            "name": "John Doe",
            "phone_number": "+1234567890",
            "email": "john@example.com"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
