from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.deps import CurrentUser
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_status_history import OrderStatusHistory
from app.schemas.payment import PaymentInitiateRequest
from app.services.payment_service import (
    generate_esewa_signature,
    initiate_esewa_payment,
    initiate_khalti_payment,
    verify_esewa_payment,
    verify_khalti_payment,
)

router = APIRouter(tags=["payments"])


@router.post("/api/payments/initiate")
async def initiate_payment(body: PaymentInitiateRequest, session: AsyncSession = Depends(get_session), current_user: CurrentUser = None):
    result = await session.execute(select(Order).where(Order.id == body.order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if isinstance(current_user, Customer) and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if body.provider == "esewa":
        return await initiate_esewa_payment(order.id, float(order.total_amount))
    elif body.provider == "khalti":
        return await initiate_khalti_payment(order.id, float(order.total_amount))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported payment provider")


@router.get("/api/payments/callback/esewa")
async def esewa_callback(order_id: int, request: Request, session: AsyncSession = Depends(get_session)):
    encoded_data = request.query_params.get("data")
    if not encoded_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing data parameter from eSewa")

    import base64
    import json as json_mod
    try:
        decoded_bytes = base64.b64decode(encoded_data)
        esewa_response = json_mod.loads(decoded_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid data from eSewa")

    status_value = esewa_response.get("status")
    ref_id = esewa_response.get("transaction_code")
    total_amount = esewa_response.get("total_amount")
    transaction_uuid = esewa_response.get("transaction_uuid")
    product_code = esewa_response.get("product_code")
    returned_signature = esewa_response.get("signature")

    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if status_value == "COMPLETE":
        from app.services.payment_service import generate_esewa_signature
        expected_signature = generate_esewa_signature(
            str(total_amount), transaction_uuid, product_code
        )
        if returned_signature != expected_signature:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="eSewa signature mismatch")

        if float(total_amount) != float(order.total_amount):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount mismatch — possible fraud")

    old_status = order.payment_status
    if status_value == "COMPLETE":
        order.payment_status = "paid"
        order.payment_reference = ref_id
    else:
        order.payment_status = "failed"

    session.add(order)
    session.add(OrderStatusHistory(
        order_id=order.id,
        status_type="payment",
        from_status=old_status,
        to_status=order.payment_status,
    ))
    await session.commit()

    return HTMLResponse(
        content=f"<html><body><h1>Payment {order.payment_status}</h1><p>Order #{order.id}</p></body></html>",
        status_code=200,
    )


@router.get("/api/payments/callback/khalti")
async def khalti_callback(order_id: int, request: Request, session: AsyncSession = Depends(get_session)):
    pidx = request.query_params.get("pidx")

    if not pidx:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing pidx parameter")

    verification = await verify_khalti_payment(pidx)
    khalti_status = verification.get("status")

    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    old_status = order.payment_status
    if khalti_status == "Completed":
        verified_amount = int(verification.get("total_amount", 0))
        expected_paisa = int(float(order.total_amount) * 100)
        if verified_amount != expected_paisa:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount mismatch — possible fraud")

        order.payment_status = "paid"
        order.payment_reference = pidx
    else:
        order.payment_status = "failed"

    session.add(order)
    session.add(OrderStatusHistory(
        order_id=order.id,
        status_type="payment",
        from_status=old_status,
        to_status=order.payment_status,
    ))
    await session.commit()

    return HTMLResponse(
        content=f"<html><body><h1>Payment {order.payment_status}</h1><p>Order #{order.id}</p></body></html>",
        status_code=200,
    )
