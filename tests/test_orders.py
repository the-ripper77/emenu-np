import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_create_order(client: AsyncClient, admin_token: str):
    cat = await client.post(
        "/api/admin/categories",
        json={"name": "Order Test", "sort_order": 10},
        headers=auth_header(admin_token),
    )
    item = await client.post(
        "/api/admin/menu-items",
        json={"category_id": cat.json()["id"], "name": "Burger", "price": 500},
        headers=auth_header(admin_token),
    )

    response = await client.post(
        "/api/orders",
        json={
            "order_type": "dine_in",
            "table_number": "5",
            "payment_method": "cash",
            "items": [{"menu_item_id": item.json()["id"], "quantity": 2}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_amount"] == 1000
    assert data["fulfillment_status"] == "received"


@pytest.mark.asyncio
async def test_create_order_with_campaign(client: AsyncClient, admin_token: str):
    cat = await client.post(
        "/api/admin/categories",
        json={"name": "Campaign Test", "sort_order": 11},
        headers=auth_header(admin_token),
    )
    item = await client.post(
        "/api/admin/menu-items",
        json={"category_id": cat.json()["id"], "name": "Pizza", "price": 1000},
        headers=auth_header(admin_token),
    )

    campaign = await client.post(
        "/api/admin/campaigns",
        json={
            "name": "Flat 100 off",
            "code": "FLAT100",
            "discount_type": "fixed_amount",
            "discount_value": 100,
        },
        headers=auth_header(admin_token),
    )

    response = await client.post(
        "/api/orders",
        json={
            "order_type": "pickup",
            "payment_method": "cash",
            "campaign_code": "FLAT100",
            "items": [{"menu_item_id": item.json()["id"], "quantity": 1}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["discount_amount"] == 100
    assert data["total_amount"] == 900


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient, admin_token: str):
    response = await client.get("/api/orders", headers=auth_header(admin_token))
    assert response.status_code == 200
