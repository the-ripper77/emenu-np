import datetime
import hashlib

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.database import get_session
from app.deps import CurrentUser, get_current_user, require_current_user
from app.models.customer import Customer
from app.models.customer_password_reset_token import CustomerPasswordResetToken
from app.models.staff_password_reset_token import StaffPasswordResetToken
from app.models.trusted_device import TrustedDevice
from app.models.user import User
from app.schemas.auth import (
    CustomerLoginRequest,
    CustomerRegisterRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    StaffLoginRequest,
    TokenResponse,
    UnifiedLoginRequest,
)
from app.services.auth_service import (
    create_access_token,
    generate_reset_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.services.email_service import send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def _is_trusted_device(session: AsyncSession, user_type: str, user_id: int, request: Request) -> bool:
    trusted_token = request.headers.get("X-Trusted-Token")
    if not trusted_token:
        return False
    result = await session.execute(
        select(TrustedDevice).where(
            TrustedDevice.user_type == user_type,
            TrustedDevice.user_id == user_id,
        )
    )
    for td in result.scalars().all():
        if td.token_hash == _hash_token(trusted_token) and td.expires_at.replace(tzinfo=datetime.UTC) > datetime.datetime.now(datetime.UTC):
            return True
    return False


@router.post("/login", response_model=TokenResponse)
async def staff_login(body: StaffLoginRequest, request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    if user.totp_enabled:
        is_trusted = await _is_trusted_device(session, "staff", user.id, request)
        if not is_trusted:
            temp_token = create_access_token(subject=str(user.id), role=user.role, user_type="staff", expires_minutes=5)
            return TokenResponse(access_token="", role=user.role, user_type="staff", requires_totp=True, temp_token=temp_token)

    token = create_access_token(subject=str(user.id), role=user.role, user_type="staff")
    return TokenResponse(access_token=token, role=user.role, user_type="staff")


@router.post("/customer/register", response_model=TokenResponse)
async def customer_register(body: CustomerRegisterRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Customer).where(Customer.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    customer = Customer(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
    )
    session.add(customer)
    await session.commit()
    await session.refresh(customer)

    token = create_access_token(subject=str(customer.id), role="customer", user_type="customer")
    return TokenResponse(access_token=token, user_type="customer")


@router.post("/customer/login", response_model=TokenResponse)
async def customer_login(body: CustomerLoginRequest, request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Customer).where(Customer.email == body.email))
    customer = result.scalar_one_or_none()
    if customer is None or customer.password_hash is None or not verify_password(body.password, customer.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if customer.totp_enabled:
        is_trusted = await _is_trusted_device(session, "customer", customer.id, request)
        if not is_trusted:
            temp_token = create_access_token(subject=str(customer.id), role="customer", user_type="customer", expires_minutes=5)
            return TokenResponse(access_token="", user_type="customer", requires_totp=True, temp_token=temp_token)

    token = create_access_token(subject=str(customer.id), role="customer", user_type="customer")
    return TokenResponse(access_token=token, user_type="customer")


@router.post("/login-all", response_model=TokenResponse)
async def unified_login(body: UnifiedLoginRequest, request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Customer).where(Customer.email == body.email))
    customer = result.scalar_one_or_none()
    if customer is not None and customer.password_hash is not None and verify_password(body.password, customer.password_hash):
        if customer.totp_enabled:
            is_trusted = await _is_trusted_device(session, "customer", customer.id, request)
            if not is_trusted:
                temp_token = create_access_token(subject=str(customer.id), role="customer", user_type="customer", expires_minutes=5)
                return TokenResponse(access_token="", user_type="customer", requires_totp=True, temp_token=temp_token)
        token = create_access_token(subject=str(customer.id), role="customer", user_type="customer")
        return TokenResponse(access_token=token, user_type="customer")

    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is not None and verify_password(body.password, user.password_hash):
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        if user.totp_enabled:
            is_trusted = await _is_trusted_device(session, "staff", user.id, request)
            if not is_trusted:
                temp_token = create_access_token(subject=str(user.id), role=user.role, user_type="staff", expires_minutes=5)
                return TokenResponse(access_token="", role=user.role, user_type="staff", requires_totp=True, temp_token=temp_token)
        token = create_access_token(subject=str(user.id), role=user.role, user_type="staff")
        return TokenResponse(access_token=token, role=user.role, user_type="staff")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(require_current_user)):
    if isinstance(current_user, User):
        token = create_access_token(subject=str(current_user.id), role=current_user.role, user_type="staff")
        return TokenResponse(access_token=token, role=current_user.role, user_type="staff")
    else:
        token = create_access_token(subject=str(current_user.id), role="customer", user_type="customer")
        return TokenResponse(access_token=token, user_type="customer")


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def staff_forgot_password(body: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user:
        await session.execute(
            delete(StaffPasswordResetToken).where(
                StaffPasswordResetToken.user_id == user.id,
                StaffPasswordResetToken.used == False,
            )
        )
        raw_token = generate_reset_token()
        token_record = StaffPasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
        )
        session.add(token_record)
        await session.commit()
        await send_password_reset_email(user.email, raw_token, user_type="staff")

    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def staff_reset_password(body: ResetPasswordRequest, session: AsyncSession = Depends(get_session)):
    token_hash = hash_token(body.token)
    result = await session.execute(
        select(StaffPasswordResetToken).where(
            StaffPasswordResetToken.token_hash == token_hash,
            StaffPasswordResetToken.used == False,
        )
    )
    record = result.scalar_one_or_none()

    if not record or datetime.datetime.now(datetime.UTC) > record.expires_at.replace(tzinfo=datetime.UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    record.used = True
    session.add(record)

    result = await session.execute(select(User).where(User.id == record.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.password_hash = hash_password(body.new_password)
    session.add(user)

    await session.execute(
        delete(StaffPasswordResetToken).where(
            StaffPasswordResetToken.user_id == user.id,
            StaffPasswordResetToken.id != record.id,
        )
    )
    await session.commit()
    return {"detail": "Password reset successful"}


@router.post("/customer/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def customer_forgot_password(body: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Customer).where(Customer.email == body.email))
    customer = result.scalar_one_or_none()

    if customer:
        await session.execute(
            delete(CustomerPasswordResetToken).where(
                CustomerPasswordResetToken.customer_id == customer.id,
                CustomerPasswordResetToken.used == False,
            )
        )
        raw_token = generate_reset_token()
        token_record = CustomerPasswordResetToken(
            customer_id=customer.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
        )
        session.add(token_record)
        await session.commit()
        await send_password_reset_email(customer.email, raw_token, user_type="customer")

    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/customer/reset-password")
async def customer_reset_password(body: ResetPasswordRequest, session: AsyncSession = Depends(get_session)):
    token_hash = hash_token(body.token)
    result = await session.execute(
        select(CustomerPasswordResetToken).where(
            CustomerPasswordResetToken.token_hash == token_hash,
            CustomerPasswordResetToken.used == False,
        )
    )
    record = result.scalar_one_or_none()

    if not record or datetime.datetime.now(datetime.UTC) > record.expires_at.replace(tzinfo=datetime.UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    record.used = True
    session.add(record)

    result = await session.execute(select(Customer).where(Customer.id == record.customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer not found")

    customer.password_hash = hash_password(body.new_password)
    session.add(customer)

    await session.execute(
        delete(CustomerPasswordResetToken).where(
            CustomerPasswordResetToken.customer_id == customer.id,
            CustomerPasswordResetToken.id != record.id,
        )
    )
    await session.commit()
    return {"detail": "Password reset successful"}
