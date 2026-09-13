from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.deps import CurrentAdmin
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import User
from app.schemas.auth import AdminPasswordResetRequest, StaffCreateRequest
from app.schemas.admin import PermissionResponse, RolePermissionsUpdate, StaffUpdateRequest
from app.services.auth_service import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(Permission))
    return result.scalars().all()


@router.get("/staff")
async def list_staff(session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "is_active": u.is_active}
        for u in users
    ]


@router.post("/staff")
async def create_staff(body: StaffCreateRequest, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@router.put("/staff/{staff_id}")
async def update_staff(staff_id: int, body: StaffUpdateRequest, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(User).where(User.id == staff_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    if body.name is not None:
        user.name = body.name
    if body.email is not None:
        user.email = body.email
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active

    session.add(user)
    await session.commit()
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "is_active": user.is_active}


@router.get("/roles/{role}/permissions")
async def get_role_permissions(role: str, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role == role)
    )
    return result.scalars().all()


@router.put("/roles/{role}/permissions")
async def update_role_permissions(role: str, body: RolePermissionsUpdate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(RolePermission).where(RolePermission.role == role))
    for rp in result.scalars().all():
        await session.delete(rp)

    for perm_id in body.permission_ids:
        session.add(RolePermission(role=role, permission_id=perm_id))

    await session.commit()
    return {"role": role, "permission_ids": body.permission_ids}


@router.put("/staff/{staff_id}/password")
async def admin_reset_staff_password(
    staff_id: int,
    body: AdminPasswordResetRequest,
    session: AsyncSession = Depends(get_session),
    _admin: CurrentAdmin = None,
):
    result = await session.execute(select(User).where(User.id == staff_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    user.password_hash = hash_password(body.new_password)
    session.add(user)
    await session.commit()
    return {"detail": "Password updated successfully"}
