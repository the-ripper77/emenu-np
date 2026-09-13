import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, admin_token: str):
    response = await client.post(
        "/api/admin/categories",
        json={"name": "Starters", "sort_order": 1},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Starters"


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, admin_token: str):
    await client.post(
        "/api/admin/categories",
        json={"name": "Mains", "sort_order": 2},
        headers=auth_header(admin_token),
    )
    response = await client.get("/api/categories")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_create_menu_item(client: AsyncClient, admin_token: str):
    cat = await client.post(
        "/api/admin/categories",
        json={"name": "Drinks", "sort_order": 3},
        headers=auth_header(admin_token),
    )
    cat_id = cat.json()["id"]

    response = await client.post(
        "/api/admin/menu-items",
        json={"category_id": cat_id, "name": "Cola", "price": 150},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Cola"


@pytest.mark.asyncio
async def test_list_menu_items(client: AsyncClient, admin_token: str):
    cat = await client.post(
        "/api/admin/categories",
        json={"name": "Snacks", "sort_order": 4},
        headers=auth_header(admin_token),
    )
    await client.post(
        "/api/admin/menu-items",
        json={"category_id": cat.json()["id"], "name": "Chips", "price": 100},
        headers=auth_header(admin_token),
    )
    response = await client.get("/api/menu-items")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_unauthorized_menu_item_create(client: AsyncClient, staff_token: str):
    response = await client.post(
        "/api/admin/menu-items",
        json={"category_id": 1, "name": "Test", "price": 100},
        headers=auth_header(staff_token),
    )
    assert response.status_code == 403
