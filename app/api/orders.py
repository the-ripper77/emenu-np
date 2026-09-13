from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.database import get_session
from app.deps import CurrentUser, require_permission
from app.models.campaign import Campaign
from app.models.customer import Customer
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.user import User
from app.schemas.order import FulfillmentUpdate, OrderCreate, PaymentStatusUpdate

router = APIRouter(tags=["orders"])


@router.post("/api/orders")
async def create_order(body: OrderCreate, session: AsyncSession = Depends(get_session), current_user: CurrentUser = None):
    if not body.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must have at least one item")

    customer_id = None
    if isinstance(current_user, Customer):
        customer_id = current_user.id

    subtotal = 0.0
    order_items_data = []
    for item in body.items:
        result = await session.execute(select(MenuItem).where(MenuItem.id == item.menu_item_id))
        menu_item = result.scalar_one_or_none()
        if menu_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item {item.menu_item_id} not found")
        if not menu_item.is_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Menu item '{menu_item.name}' is not available")

        item_total = float(menu_item.price) * item.quantity
        subtotal += item_total
        order_items_data.append({
            "menu_item_id": menu_item.id,
            "quantity": item.quantity,
            "price_at_order": float(menu_item.price),
        })

    total = subtotal + (body.delivery_fee or 0)

    campaign_id = None
    discount_amount = None
    if body.campaign_code:
        result = await session.execute(
            select(Campaign).where(Campaign.code == body.campaign_code, Campaign.is_active == True)
        )
        campaign = result.scalar_one_or_none()
        if campaign is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid campaign code")

        if campaign.usage_limit_total:
            count_result = await session.execute(
                select(func.count(Order.id)).where(Order.campaign_id == campaign.id)
            )
            if (count_result.scalar() or 0) >= campaign.usage_limit_total:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign usage limit reached")

        if campaign.usage_limit_per_customer and customer_id:
            count_result = await session.execute(
                select(func.count(Order.id)).where(
                    Order.campaign_id == campaign.id, Order.customer_id == customer_id
                )
            )
            if (count_result.scalar() or 0) >= campaign.usage_limit_per_customer:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already used this campaign")

        if campaign.discount_type == "percentage":
            discount = total * (float(campaign.discount_value) / 100)
            if campaign.max_discount_amount:
                discount = min(discount, float(campaign.max_discount_amount))
        else:
            discount = float(campaign.discount_value)

        discount = min(discount, total)
        discount_amount = round(discount, 2)
        total -= discount
        campaign_id = campaign.id

    total = round(total, 2)

    order = Order(
        customer_id=customer_id,
        order_type=body.order_type,
        table_number=body.table_number,
        delivery_address=body.delivery_address,
        delivery_fee=body.delivery_fee,
        scheduled_for=body.scheduled_for,
        payment_method=body.payment_method,
        payment_provider=body.payment_provider,
        total_amount=total,
        campaign_id=campaign_id,
        discount_amount=discount_amount,
        payment_status="pending" if body.payment_method != "cash" else "pending",
        fulfillment_status="received",
    )
    session.add(order)
    await session.flush()

    for item_data in order_items_data:
        session.add(OrderItem(order_id=order.id, **item_data))

    session.add(OrderStatusHistory(
        order_id=order.id,
        status_type="fulfillment",
        from_status=None,
        to_status="received",
        changed_by_user_id=current_user.id if isinstance(current_user, User) else None,
    ))

    if body.payment_method == "cash":
        order.payment_status = "pending"

    await session.commit()
    await session.refresh(order)

    return {
        "id": order.id,
        "total_amount": order.total_amount,
        "payment_status": order.payment_status,
        "fulfillment_status": order.fulfillment_status,
        "discount_amount": order.discount_amount,
    }


@router.get("/api/orders")
async def list_orders(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
):
    if isinstance(current_user, Customer):
        result = await session.execute(
            select(Order).where(Order.customer_id == current_user.id).order_by(Order.created_at.desc())
        )
    else:
        result = await session.execute(select(Order).order_by(Order.created_at.desc()))

    orders = result.scalars().all()
    return [
        {
            "id": o.id,
            "order_type": o.order_type,
            "payment_status": o.payment_status,
            "fulfillment_status": o.fulfillment_status,
            "total_amount": o.total_amount,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


@router.get("/api/orders/{order_id}")
async def get_order(order_id: int, session: AsyncSession = Depends(get_session), current_user: CurrentUser = None):
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if isinstance(current_user, Customer) and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    items_result = await session.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    items = items_result.scalars().all()

    history_result = await session.execute(
        select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id).order_by(OrderStatusHistory.changed_at)
    )
    history = history_result.scalars().all()

    return {
        "id": order.id,
        "order_type": order.order_type,
        "table_number": order.table_number,
        "delivery_address": order.delivery_address,
        "delivery_fee": order.delivery_fee,
        "scheduled_for": order.scheduled_for.isoformat() if order.scheduled_for else None,
        "payment_method": order.payment_method,
        "payment_provider": order.payment_provider,
        "payment_status": order.payment_status,
        "payment_reference": order.payment_reference,
        "fulfillment_status": order.fulfillment_status,
        "total_amount": order.total_amount,
        "discount_amount": order.discount_amount,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "items": [
            {"id": i.id, "menu_item_id": i.menu_item_id, "quantity": i.quantity, "price_at_order": i.price_at_order}
            for i in items
        ],
        "status_history": [
            {
                "status_type": h.status_type,
                "from_status": h.from_status,
                "to_status": h.to_status,
                "changed_at": h.changed_at.isoformat() if h.changed_at else None,
            }
            for h in history
        ],
    }


@router.patch("/api/orders/{order_id}/fulfillment")
async def update_fulfillment(
    order_id: int,
    body: FulfillmentUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("update_fulfillment_status")),
):
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    old_status = order.fulfillment_status
    order.fulfillment_status = body.fulfillment_status
    session.add(order)

    session.add(OrderStatusHistory(
        order_id=order.id,
        status_type="fulfillment",
        from_status=old_status,
        to_status=body.fulfillment_status,
        changed_by_user_id=current_user.id,
    ))

    await session.commit()

    if body.fulfillment_status == "completed" and order.customer_id:
        from app.models.customer import Customer
        from app.models.order_item import OrderItem
        from app.models.menu_item import MenuItem
        from app.services.email_service import send_invoice_email

        cust_result = await session.execute(select(Customer).where(Customer.id == order.customer_id))
        customer = cust_result.scalar_one_or_none()

        if customer and customer.email and customer.email_verified:
            items_result = await session.execute(select(OrderItem).where(OrderItem.order_id == order.id))
            order_items = items_result.scalars().all()

            items_data = []
            for oi in order_items:
                mi_result = await session.execute(select(MenuItem).where(MenuItem.id == oi.menu_item_id))
                mi = mi_result.scalar_one_or_none()
                items_data.append({
                    "name": mi.name if mi else f"Item #{oi.menu_item_id}",
                    "quantity": oi.quantity,
                    "price_at_order": float(oi.price_at_order),
                })

            subtotal = sum(i["quantity"] * i["price_at_order"] for i in items_data)
            await send_invoice_email(
                to=customer.email,
                customer_name=customer.name or "Customer",
                order_id=order.id,
                items=items_data,
                subtotal=subtotal,
                discount_amount=float(order.discount_amount) if order.discount_amount else None,
                delivery_fee=float(order.delivery_fee) if order.delivery_fee else None,
                total=float(order.total_amount),
                order_type=order.order_type,
                payment_method=order.payment_method,
                payment_status=order.payment_status,
            )

    return {"id": order.id, "fulfillment_status": order.fulfillment_status}


@router.patch("/api/orders/{order_id}/payment-status")
async def update_payment_status(
    order_id: int,
    body: PaymentStatusUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_permission("verify_payment")),
):
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    old_status = order.payment_status
    order.payment_status = body.payment_status
    if body.payment_reference:
        order.payment_reference = body.payment_reference
    if body.payment_status == "paid":
        order.verified_by_user_id = current_user.id
        from datetime import datetime, timezone
        order.verified_at = datetime.now(timezone.utc)

    session.add(order)

    session.add(OrderStatusHistory(
        order_id=order.id,
        status_type="payment",
        from_status=old_status,
        to_status=body.payment_status,
        changed_by_user_id=current_user.id,
    ))

    await session.commit()
    return {"id": order.id, "payment_status": order.payment_status}
