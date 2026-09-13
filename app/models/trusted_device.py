import datetime
import secrets
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class TrustedDevice(SQLModel, table=True):
    __tablename__ = "trusted_devices"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_type: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    user_id: int = Field(sa_column=sa.Column(sa.Integer, nullable=False))
    token_hash: str = Field(sa_column=sa.Column(sa.Text, unique=True, nullable=False))
    user_agent: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    ip_address: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    expires_at: datetime.datetime = Field(sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False))
    created_at: datetime.datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    )
