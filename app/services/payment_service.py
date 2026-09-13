import base64
import hashlib
import hmac
import uuid

import httpx

from app.config import settings


def generate_esewa_signature(total_amount: str, transaction_uuid: str, product_code: str) -> str:
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    signature = hmac.new(
        settings.ESEWA_SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(signature).decode("utf-8")


async def initiate_esewa_payment(order_id: int, total_amount: float) -> dict:
    transaction_uuid = f"emenu-{order_id}-{uuid.uuid4().hex[:8]}"
    product_code = settings.ESEWA_MERCHANT_ID
    total_str = f"{total_amount:.2f}"

    signature = generate_esewa_signature(total_str, transaction_uuid, product_code)

    form_data = {
        "amount": f"{total_amount:.2f}",
        "tax_amount": "0.00",
        "total_amount": total_str,
        "transaction_uuid": transaction_uuid,
        "product_code": product_code,
        "product_service_charge": "0.00",
        "product_delivery_charge": "0.00",
        "success_url": f"{settings.APP_BASE_URL}/api/payments/callback/esewa?order_id={order_id}",
        "failure_url": f"{settings.APP_BASE_URL}/api/payments/callback/esewa?order_id={order_id}",
        "signed_field_names": "total_amount,transaction_uuid,product_code",
        "signature": signature,
    }

    return {
        "provider": "esewa",
        "redirect_url": f"{settings.ESEWA_BASE_URL}/api/epay/main/v2/form",
        "form_data": form_data,
    }


async def verify_esewa_payment(product_code: str, total_amount: str, transaction_uuid: str) -> dict:
    url = f"{settings.ESEWA_BASE_URL}/api/epay/transaction/status/"
    params = {
        "product_code": product_code,
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()


async def initiate_khalti_payment(order_id: int, total_amount: float, customer_name: str = "Customer", customer_phone: str = "9800000000") -> dict:
    amount_paisa = int(total_amount * 100)

    url = f"{settings.KHALTI_BASE_URL}/epayment/initiate/"
    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "return_url": f"{settings.APP_BASE_URL}/api/payments/callback/khalti?order_id={order_id}",
        "website_url": settings.APP_BASE_URL,
        "amount": str(amount_paisa),
        "purchase_order_id": str(order_id),
        "purchase_order_name": f"Order #{order_id}",
        "customer_info": {
            "name": customer_name,
            "email": "customer@emenu.com",
            "phone": customer_phone,
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()


async def verify_khalti_payment(pidx: str) -> dict:
    url = f"{settings.KHALTI_BASE_URL}/epayment/lookup/"
    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"pidx": pidx}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()
