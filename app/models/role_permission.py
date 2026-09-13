from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    role: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    permission_id: int = Field(sa_column=sa.Column(sa.Integer, sa.ForeignKey("permissions.id"), nullable=False))
