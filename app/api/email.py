import datetime
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.database import get_session
from app.deps import CurrentUser
from app.models.customer import Customer
from app.models.email_verification import EmailVerification
from app.schemas.email import EmailRequest, VerifyEmailRequest
from app.services.email_service import send_otp_email

router = APIRouter(tags=["email"])


def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


@router.post("/api/customer/email/request-verification")
async def request_email_verification(
    body: EmailRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
):
    if current_user is None or isinstance(current_user, Customer) is False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer auth required")

    customer = current_user
    code = generate_otp()
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    verification = EmailVerification(
        customer_id=customer.id,
        email=body.email,
        code=code,
        purpose="verify_email",
        expires_at=expires_at,
    )
    session.add(verification)
    await session.commit()

    await send_otp_email(body.email, code, purpose="verify your email address")

    return {"detail": "Verification code sent", "email": body.email}


@router.post("/api/customer/email/verify")
async def verify_email(
    body: VerifyEmailRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
):
    if current_user is None or isinstance(current_user, Customer) is False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer auth required")

    customer = current_user

    result = await session.execute(
        select(EmailVerification).where(
            EmailVerification.customer_id == customer.id,
            EmailVerification.email == body.email,
            EmailVerification.code == body.code,
            EmailVerification.purpose == "verify_email",
            EmailVerification.used == False,
        ).order_by(EmailVerification.id.desc())
    )
    verification = result.scalar_one_or_none()

    if verification is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    if datetime.datetime.now(datetime.UTC) > verification.expires_at.replace(tzinfo=datetime.UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")

    verification.used = True
    session.add(verification)

    customer.email = body.email
    customer.email_verified = True
    session.add(customer)

    await session.commit()

    return {"detail": "Email verified successfully", "email": body.email}
