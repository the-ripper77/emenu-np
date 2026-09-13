from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    sort_order: int = Field(default=0, sa_column=sa.Column(sa.Integer, nullable=False, server_default="0"))
