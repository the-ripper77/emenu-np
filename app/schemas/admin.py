from typing import Optional

from pydantic import BaseModel


class PermissionResponse(BaseModel):
    id: int
    key: str
    description: str


class RolePermissionsUpdate(BaseModel):
    permission_ids: list[int]


class StaffUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
