from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class MenuItem(SQLModel, table=True):
    __tablename__ = "menu_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(sa_column=sa.Column(sa.Integer, sa.ForeignKey("categories.id"), nullable=False))
    name: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    description: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    price: float = Field(sa_column=sa.Column(sa.Numeric(10, 2), nullable=False))
    image_url: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    is_available: bool = Field(default=True, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="true"))
    sort_order: int = Field(default=0, sa_column=sa.Column(sa.Integer, nullable=False, server_default="0"))
