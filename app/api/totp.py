import datetime
import hashlib
import secrets

import pyotp
import io
import base64
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.deps import CurrentUser, require_current_user
from app.models.customer import Customer
from app.models.user import User
from app.models.trusted_device import TrustedDevice
from app.schemas.auth import VerifyTOTPRequest, DisableTOTPRequest

router = APIRouter(prefix="/api/totp", tags=["totp"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/setup")
async def setup_totp(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if isinstance(current_user, User):
        user_type = "staff"
        user_id = current_user.id
        if current_user.totp_enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP already enabled")
        user = current_user
    else:
        user_type = "customer"
        user_id = current_user.id
        if current_user.totp_enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP already enabled")
        user = current_user

    secret = pyotp.random_base32()
    user.totp_secret = secret
    session.add(user)
    await session.commit()

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="eMenu",
    )

    import qrcode
    qr = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_code": f"data:image/png;base64,{qr_b64}",
    }


@router.post("/verify")
async def verify_and_enable_totp(
    body: VerifyTOTPRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if isinstance(current_user, User):
        user = current_user
    else:
        user = current_user

    if not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP setup not initiated")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    user.totp_enabled = True
    user.totp_enabled_at = datetime.datetime.now(datetime.UTC)
    session.add(user)
    await session.commit()

    return {"detail": "TOTP enabled successfully"}


@router.post("/disable")
async def disable_totp(
    body: DisableTOTPRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if isinstance(current_user, User):
        user = current_user
    else:
        user = current_user

    if not user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP not enabled")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    user.totp_secret = None
    user.totp_enabled = False
    user.totp_enabled_at = None
    session.add(user)

    await session.execute(
        select(TrustedDevice).where(
            TrustedDevice.user_type == ("staff" if isinstance(current_user, User) else "customer"),
            TrustedDevice.user_id == user.id,
        )
    )
    for td in (await session.execute(select(TrustedDevice).where(
        TrustedDevice.user_type == ("staff" if isinstance(current_user, User) else "customer"),
        TrustedDevice.user_id == user.id,
    ))).scalars().all():
        await session.delete(td)

    await session.commit()
    return {"detail": "TOTP disabled successfully"}


@router.post("/verify-login")
async def verify_totp_login(
    body: VerifyTOTPRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    if not body.temp_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="temp_token required")

    from app.services.auth_service import decode_token
    payload = decode_token(body.temp_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid temp token")

    user_type = payload.get("user_type", "staff")
    user_id = int(payload["sub"])

    if user_type == "staff":
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    else:
        result = await session.execute(select(Customer).where(Customer.id == user_id))
        user = result.scalar_one_or_none()

    if user is None or not user.totp_enabled or not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP not enabled for this user")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")

    if body.remember_device:
        trusted_token = secrets.token_urlsafe(32)
        trusted_token_hash = _hash_token(trusted_token)
        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)

        td = TrustedDevice(
            user_type=user_type,
            user_id=user_id,
            token_hash=trusted_token_hash,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            expires_at=expires_at,
        )
        session.add(td)
        await session.commit()

    from app.services.auth_service import create_access_token
    token = create_access_token(subject=str(user.id), role=user.role if isinstance(user, User) else "customer", user_type=user_type)

    response = {"access_token": token, "token_type": "bearer", "user_type": user_type}
    if body.remember_device:
        response["trusted_token"] = trusted_token

    return response


@router.get("/trusted-devices")
async def list_trusted_devices(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if isinstance(current_user, User):
        user_type, user_id = "staff", current_user.id
    else:
        user_type, user_id = "customer", current_user.id

    result = await session.execute(
        select(TrustedDevice).where(
            TrustedDevice.user_type == user_type,
            TrustedDevice.user_id == user_id,
        ).order_by(TrustedDevice.created_at.desc())
    )
    devices = result.scalars().all()
    return [
        {
            "id": d.id,
            "user_agent": d.user_agent,
            "ip_address": d.ip_address,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "expires_at": d.expires_at.isoformat() if d.expires_at else None,
        }
        for d in devices
    ]


@router.delete("/trusted-devices/{device_id}")
async def delete_trusted_device(
    device_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if isinstance(current_user, User):
        user_type, user_id = "staff", current_user.id
    else:
        user_type, user_id = "customer", current_user.id

    result = await session.execute(
        select(TrustedDevice).where(
            TrustedDevice.id == device_id,
            TrustedDevice.user_type == user_type,
            TrustedDevice.user_id == user_id,
        )
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trusted device not found")

    await session.delete(device)
    await session.commit()
    return {"detail": "Trusted device deleted"}


@router.delete("/trusted-devices")
async def delete_all_trusted_devices(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if isinstance(current_user, User):
        user_type, user_id = "staff", current_user.id
    else:
        user_type, user_id = "customer", current_user.id

    result = await session.execute(
        select(TrustedDevice).where(
            TrustedDevice.user_type == user_type,
            TrustedDevice.user_id == user_id,
        )
    )
    for device in result.scalars().all():
        await session.delete(device)
    await session.commit()
    return {"detail": "All trusted devices deleted"}
