import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class OrderStatusHistory(SQLModel, table=True):
    __tablename__ = "order_status_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(sa_column=sa.Column(sa.Integer, sa.ForeignKey("orders.id"), nullable=False))
    status_type: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    from_status: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    to_status: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    changed_by_user_id: Optional[int] = Field(default=None, sa_column=sa.Column(sa.Integer, sa.ForeignKey("users.id")))
    changed_at: datetime.datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    )
