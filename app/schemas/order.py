from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int


class OrderCreate(BaseModel):
    order_type: str
    table_number: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_fee: Optional[float] = None
    scheduled_for: Optional[datetime] = None
    payment_method: str
    payment_provider: Optional[str] = None
    campaign_code: Optional[str] = None
    items: list[OrderItemCreate]


class FulfillmentUpdate(BaseModel):
    fulfillment_status: str


class PaymentStatusUpdate(BaseModel):
    payment_status: str
    payment_reference: Optional[str] = None
