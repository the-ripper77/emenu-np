import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class StaffPasswordResetToken(SQLModel, table=True):
    __tablename__ = "staff_password_reset_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False))
    token_hash: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    expires_at: datetime.datetime = Field(sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False))
    used: bool = Field(default=False, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="false"))
    created_at: datetime.datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    )
