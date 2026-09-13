import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient, admin_token: str):
    response = await client.post(
        "/api/admin/campaigns",
        json={
            "name": "New Year Sale",
            "code": "NY2025",
            "discount_type": "percentage",
            "discount_value": 20,
            "max_discount_amount": 200,
        },
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["code"] == "NY2025"


@pytest.mark.asyncio
async def test_validate_campaign(client: AsyncClient, admin_token: str):
    await client.post(
        "/api/admin/campaigns",
        json={
            "name": "Test Campaign",
            "code": "TEST10",
            "discount_type": "percentage",
            "discount_value": 10,
        },
        headers=auth_header(admin_token),
    )

    response = await client.post(
        "/api/campaigns/validate",
        json={"code": "TEST10", "order_total": 500},
    )
    assert response.status_code == 200
    assert response.json()["discount_amount"] == 50


@pytest.mark.asyncio
async def test_validate_invalid_code(client: AsyncClient):
    response = await client.post(
        "/api/campaigns/validate",
        json={"code": "INVALID", "order_total": 500},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_campaign_usage_limit(client: AsyncClient, admin_token: str):
    await client.post(
        "/api/admin/campaigns",
        json={
            "name": "Limited",
            "code": "LIMITED",
            "discount_type": "fixed_amount",
            "discount_value": 50,
            "usage_limit_total": 1,
        },
        headers=auth_header(admin_token),
    )

    cat = await client.post(
        "/api/admin/categories",
        json={"name": "Limit Test", "sort_order": 20},
        headers=auth_header(admin_token),
    )
    item = await client.post(
        "/api/admin/menu-items",
        json={"category_id": cat.json()["id"], "name": "Item", "price": 200},
        headers=auth_header(admin_token),
    )

    await client.post(
        "/api/orders",
        json={
            "order_type": "pickup",
            "payment_method": "cash",
            "campaign_code": "LIMITED",
            "items": [{"menu_item_id": item.json()["id"], "quantity": 1}],
        },
    )

    response = await client.post(
        "/api/orders",
        json={
            "order_type": "pickup",
            "payment_method": "cash",
            "campaign_code": "LIMITED",
            "items": [{"menu_item_id": item.json()["id"], "quantity": 1}],
        },
    )
    assert response.status_code == 400
