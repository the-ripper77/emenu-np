import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Customer(SQLModel, table=True):
    __tablename__ = "customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(sa_column=sa.Column(sa.Text, unique=True, nullable=False))
    password_hash: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    name: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    phone_number: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    phone_verified: bool = Field(default=False, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="false"))
    email_verified: bool = Field(default=False, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="false"))
    totp_secret: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    totp_enabled: bool = Field(default=False, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="false"))
    totp_enabled_at: Optional[datetime.datetime] = Field(default=None, sa_column=sa.Column(sa.DateTime(timezone=True)))
    created_at: datetime.datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    )
