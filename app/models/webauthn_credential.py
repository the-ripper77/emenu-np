import datetime
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class WebAuthnCredential(SQLModel, table=True):
    __tablename__ = "webauthn_credentials"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_type: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    user_id: int = Field(sa_column=sa.Column(sa.Integer, nullable=False))
    credential_id: str = Field(sa_column=sa.Column(sa.Text, unique=True, nullable=False))
    public_key: bytes = Field(sa_column=sa.Column(sa.LargeBinary, nullable=False))
    sign_count: int = Field(default=0, sa_column=sa.Column(sa.Integer, nullable=False, server_default="0"))
    aaguid: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    credential_device_type: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    credential_backed_up: bool = Field(default=False, sa_column=sa.Column(sa.Boolean, nullable=False, server_default="false"))
    name: Optional[str] = Field(default=None, sa_column=sa.Column(sa.Text))
    created_at: datetime.datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    )
