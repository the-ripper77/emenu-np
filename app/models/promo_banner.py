from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class PromoBanner(SQLModel, table=True):
    __tablename__ = "promo_banners"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    description: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    image_url: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    link_type: str = Field(sa_column=sa.Column(sa.Text, nullable=False, server_default="none"))
    link_target_id: Optional[int] = Field(default=None, sa_column=sa.Column(sa.Integer))
    start_date: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Date))
    end_date: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Date))
    is_active: bool = Field(default=True, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="true"))
    sort_order: int = Field(default=0, sa_column=sa.Column(sa.Integer, nullable=False, server_default="0"))
