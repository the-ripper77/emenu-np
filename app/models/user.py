import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    email: str = Field(sa_column=sa.Column(sa.Text, unique=True, nullable=False))
    password_hash: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    role: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    is_active: bool = Field(default=True, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="true"))
    totp_secret: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    totp_enabled: bool = Field(default=False, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="false"))
    totp_enabled_at: Optional[datetime.datetime] = Field(default=None, sa_column=sa.Column(sa.DateTime(timezone=True)))
    created_at: datetime.datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    )
