from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Campaign(SQLModel, table=True):
    __tablename__ = "campaigns"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    code: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text, unique=True))
    discount_type: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    discount_value: float = Field(sa_column=sa.Column(sa.Numeric(10, 2), nullable=False))
    max_discount_amount: Optional[float] = Field(default=None, sa_column=sa.Column(sa.Numeric(10, 2)))
    min_order_amount: Optional[float] = Field(default=None, sa_column=sa.Column(sa.Numeric(10, 2)))
    usage_limit_total: Optional[int] = Field(default=None, sa_column=sa.Column(sa.Integer))
    usage_limit_per_customer: Optional[int] = Field(default=None, sa_column=sa.Column(sa.Integer))
    start_date: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Date))
    end_date: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Date))
    is_active: bool = Field(default=True, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="true"))
