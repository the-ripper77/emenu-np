import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class EmailVerification(SQLModel, table=True):
    __tablename__ = "email_verifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(sa_column=sa.Column(sa.Integer, sa.ForeignKey("customers.id"), nullable=False))
    email: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    code: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    purpose: str = Field(default="verify_email", sa_column=sa.Column(sa.Text, nullable=False))
    expires_at: datetime.datetime = Field(sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False))
    used: bool = Field(default=False, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="false"))
    created_at: datetime.datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    )
