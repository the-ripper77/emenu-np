from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class RestaurantProfile(SQLModel, table=True):
    __tablename__ = "restaurant_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    logo_url: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    description: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    address: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    phone: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    business_hours: Optional[dict] = Field(default=None, sa_column=sa.Column(sa.JSON))
