from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(sa_column=sa.Column(sa.Integer, sa.ForeignKey("orders.id"), nullable=False))
    menu_item_id: int = Field(sa_column=sa.Column(sa.Integer, sa.ForeignKey("menu_items.id"), nullable=False))
    quantity: int = Field(sa_column=sa.Column(sa.Integer, nullable=False))
    price_at_order: float = Field(sa_column=sa.Column(sa.Numeric(10, 2), nullable=False))
