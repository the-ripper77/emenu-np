import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: Optional[int] = Field(default=None, sa_column=sa.Column(sa.Integer, sa.ForeignKey("customers.id")))
    order_type: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    table_number: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    delivery_address: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    delivery_fee: Optional[float] = Field(default=None, sa_column=sa.Column(sa.Numeric(10, 2)))
    scheduled_for: Optional[datetime.datetime] = Field(default=None, sa_column=sa.Column(sa.DateTime(timezone=True)))
    payment_method: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    payment_provider: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    payment_status: str = Field(default="pending", sa_column=sa.Column(sa.Text, nullable=False, server_default="pending"))
    payment_reference: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    fulfillment_status: str = Field(default="received", sa_column=sa.Column(sa.Text, nullable=False, server_default="received"))
    verified_by_user_id: Optional[int] = Field(default=None, sa_column=sa.Column(sa.Integer, sa.ForeignKey("users.id")))
    verified_at: Optional[datetime.datetime] = Field(default=None, sa_column=sa.Column(sa.DateTime(timezone=True)))
    total_amount: float = Field(sa_column=sa.Column(sa.Numeric(10, 2), nullable=False))
    campaign_id: Optional[int] = Field(default=None, sa_column=sa.Column(sa.Integer, sa.ForeignKey("campaigns.id")))
    discount_amount: Optional[float] = Field(default=None, sa_column=sa.Column(sa.Numeric(10, 2)))
    created_at: datetime.datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    )
