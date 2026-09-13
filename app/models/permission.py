from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(sa_column=sa.Column(sa.Text, unique=True, nullable=False))
    description: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
