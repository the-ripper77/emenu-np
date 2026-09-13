import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class WebAuthnChallenge(SQLModel, table=True):
    __tablename__ = "webauthn_challenges"

    id: Optional[int] = Field(default=None, primary_key=True)
    challenge: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    user_type: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    user_id: Optional[int] = Field(default=None, sa_column=sa.Column(sa.Integer))
    ceremony: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    expires_at: datetime.datetime = Field(sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False))
    used: bool = Field(default=False, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="false"))
    created_at: datetime.datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    )
