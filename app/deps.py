from typing import Annotated, Optional, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.customer import Customer
from app.models.user import User
from app.services.auth_service import decode_token

security = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Optional[Union[User, Customer]]:
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_type = payload.get("type")
    subject = payload.get("sub")

    if user_type == "staff":
        result = await session.execute(select(User).where(User.id == int(subject)))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        return user
    elif user_type == "customer":
        result = await session.execute(select(Customer).where(Customer.id == int(subject)))
        customer = result.scalar_one_or_none()
        if customer is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer not found")
        return customer

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")


CurrentUser = Annotated[Optional[Union[User, Customer]], Depends(get_current_user)]


async def require_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Union[User, Customer]:
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_type = payload.get("type")
    subject = payload.get("sub")

    if user_type == "staff":
        result = await session.execute(select(User).where(User.id == int(subject)))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        return user
    elif user_type == "customer":
        result = await session.execute(select(Customer).where(Customer.id == int(subject)))
        customer = result.scalar_one_or_none()
        if customer is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer not found")
        return customer

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")


async def get_current_admin(
    current_user: Union[User, Customer] = Depends(require_current_user),
) -> User:
    if isinstance(current_user, Customer) or current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]


async def get_current_staff(
    current_user: Union[User, Customer] = Depends(require_current_user),
) -> User:
    if isinstance(current_user, Customer) or current_user.role not in ("admin", "staff", "kitchen"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")
    return current_user


CurrentStaff = Annotated[User, Depends(get_current_staff)]


def require_permission(permission_key: str):
    async def _check(
        current_user: User = Depends(require_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        if current_user.role == "admin":
            return current_user

        from app.models.permission import Permission
        from app.models.role_permission import RolePermission

        result = await session.execute(
            select(Permission.key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role == current_user.role, Permission.key == permission_key)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission_key}")
        return current_user

    return _check
