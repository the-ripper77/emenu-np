import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_staff_login(client: AsyncClient, admin_token: str):
    response = await client.get("/api/admin/staff", headers=auth_header(admin_token))
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_customer_register_and_login(client: AsyncClient):
    reg_response = await client.post("/api/auth/customer/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test Customer",
    })
    assert reg_response.status_code == 200
    assert "access_token" in reg_response.json()

    login_response = await client.post("/api/auth/customer/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert login_response.status_code == 200
    assert login_response.json()["user_type"] == "customer"


@pytest.mark.asyncio
async def test_customer_duplicate_email(client: AsyncClient):
    await client.post("/api/auth/customer/register", json={
        "email": "dup@example.com",
        "password": "testpass123",
    })
    response = await client.post("/api/auth/customer/register", json={
        "email": "dup@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_customer_wrong_password(client: AsyncClient):
    await client.post("/api/auth/customer/register", json={
        "email": "wrong@example.com",
        "password": "testpass123",
    })
    response = await client.post("/api/auth/customer/login", json={
        "email": "wrong@example.com",
        "password": "wrongpass",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_staff_login(client: AsyncClient):
    response = await client.post("/api/auth/login", json={"email": "wrong@test.com", "password": "wrong"})
    assert response.status_code == 401
