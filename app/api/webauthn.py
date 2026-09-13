import base64
import datetime
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.database import get_session
from app.deps import CurrentUser, require_current_user
from app.models.customer import Customer
from app.models.user import User
from app.models.webauthn_credential import WebAuthnCredential
from app.models.webauthn_challenge import WebAuthnChallenge
from app.schemas.webauthn import (
    WebAuthnAuthBeginRequest,
    WebAuthnAuthFinishRequest,
    WebAuthnCredentialResponse,
    WebAuthnRegisterBeginRequest,
    WebAuthnRegisterFinishRequest,
)
from app.services.auth_service import create_access_token

router = APIRouter(prefix="/api/webauthn", tags=["webauthn"])


def _get_user_id_bytes(user_type: str, user_id: int) -> bytes:
    return f"{user_type}:{user_id}".encode("utf-8")


@router.post("/register/begin")
async def register_begin(
    body: WebAuthnRegisterBeginRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if body.user_type == "staff":
        if not isinstance(current_user, User):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff auth required")
        user_id = current_user.id
        user_email = current_user.email
    else:
        if not isinstance(current_user, Customer):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer auth required")
        user_id = current_user.id
        user_email = current_user.email

    result = await session.execute(
        select(WebAuthnCredential).where(
            WebAuthnCredential.user_type == body.user_type,
            WebAuthnCredential.user_id == user_id,
        )
    )
    existing_credentials = result.scalars().all()

    import webauthn
    options = webauthn.generate_registration_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_name=user_email,
        user_id=_get_user_id_bytes(body.user_type, user_id),
        user_display_name=user_email,
        authenticator_selection=webauthn.helpers.structs.AuthenticatorSelectionCriteria(
            resident_key=webauthn.helpers.structs.ResidentKeyRequirement.PREFERRED,
            user_verification=webauthn.helpers.structs.UserVerificationRequirement.PREFERRED,
        ),
        exclude_credentials=[
            webauthn.helpers.structs.PublicKeyCredentialDescriptor(id=bytes.fromhex(c.credential_id))
            for c in existing_credentials
        ],
    )

    challenge_b64 = base64.urlsafe_b64encode(options.challenge).decode("utf-8")
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60)

    challenge_record = WebAuthnChallenge(
        challenge=challenge_b64,
        user_type=body.user_type,
        user_id=user_id,
        ceremony="registration",
        expires_at=expires_at,
    )
    session.add(challenge_record)
    await session.commit()

    return JSONResponse(content=webauthn.options_to_json(options))


@router.post("/register/finish")
async def register_finish(
    body: WebAuthnRegisterFinishRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if body.user_type == "staff":
        if not isinstance(current_user, User):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff auth required")
        user_id = current_user.id
    else:
        if not isinstance(current_user, Customer):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer auth required")
        user_id = current_user.id

    result = await session.execute(
        select(WebAuthnChallenge).where(
            WebAuthnChallenge.user_type == body.user_type,
            WebAuthnChallenge.user_id == user_id,
            WebAuthnChallenge.ceremony == "registration",
            WebAuthnChallenge.used == False,
        ).order_by(WebAuthnChallenge.id.desc())
    )
    challenge_record = result.scalar_one_or_none()

    if not challenge_record or datetime.datetime.now(datetime.UTC) > challenge_record.expires_at.replace(tzinfo=datetime.UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Challenge expired or missing")

    challenge_record.used = True
    session.add(challenge_record)

    expected_challenge = base64.urlsafe_b64decode(challenge_record.challenge)

    import webauthn
    try:
        verification = webauthn.verify_registration_response(
            credential=body.credential,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=settings.WEBAUTHN_ORIGIN,
        )
    except webauthn.helpers.exceptions.InvalidRegistrationResponse as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Registration failed: {e}")

    cred_id_hex = verification.credential_id.hex()
    credential = WebAuthnCredential(
        user_type=body.user_type,
        user_id=user_id,
        credential_id=cred_id_hex,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        aaguid=verification.aaguid.hex() if verification.aaguid else None,
        credential_device_type=str(verification.credential_device_type),
        credential_backed_up=verification.credential_backed_up,
        name=body.email,
    )
    session.add(credential)
    await session.commit()

    return {"verified": True, "message": "Passkey registered successfully"}


@router.post("/authenticate/begin")
async def auth_begin(
    body: WebAuthnAuthBeginRequest,
    session: AsyncSession = Depends(get_session),
):
    import webauthn
    allow_credentials = []
    if body.email:
        if body.user_type == "staff":
            user_result = await session.execute(select(User).where(User.email == body.email))
            user = user_result.scalar_one_or_none()
        else:
            user_result = await session.execute(select(Customer).where(Customer.email == body.email))
            user = user_result.scalar_one_or_none()

        if user:
            cred_result = await session.execute(
                select(WebAuthnCredential).where(
                    WebAuthnCredential.user_type == body.user_type,
                    WebAuthnCredential.user_id == user.id,
                )
            )
            credentials = cred_result.scalars().all()
            allow_credentials = [
                webauthn.helpers.structs.PublicKeyCredentialDescriptor(id=bytes.fromhex(c.credential_id))
                for c in credentials
            ]

    options = webauthn.generate_authentication_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        allow_credentials=allow_credentials,
        user_verification=webauthn.helpers.structs.UserVerificationRequirement.PREFERRED,
    )

    challenge_b64 = base64.urlsafe_b64encode(options.challenge).decode("utf-8")
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60)

    challenge_record = WebAuthnChallenge(
        challenge=challenge_b64,
        user_type=body.user_type,
        user_id=None,
        ceremony="authentication",
        expires_at=expires_at,
    )
    session.add(challenge_record)
    await session.commit()

    return JSONResponse(content=webauthn.options_to_json(options))


@router.post("/authenticate/finish")
async def auth_finish(
    body: WebAuthnAuthFinishRequest,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(WebAuthnChallenge).where(
            WebAuthnChallenge.ceremony == "authentication",
            WebAuthnChallenge.used == False,
        ).order_by(WebAuthnChallenge.id.desc())
    )
    challenge_record = result.scalar_one_or_none()

    if not challenge_record or datetime.datetime.now(datetime.UTC) > challenge_record.expires_at.replace(tzinfo=datetime.UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Challenge expired or missing")

    challenge_record.used = True
    session.add(challenge_record)

    expected_challenge = base64.urlsafe_b64decode(challenge_record.challenge)

    raw_id = body.credential.get("rawId", "")
    cred_id_hex = raw_id if isinstance(raw_id, str) else raw_id.hex() if isinstance(raw_id, bytes) else ""

    cred_result = await session.execute(
        select(WebAuthnCredential).where(WebAuthnCredential.credential_id == cred_id_hex)
    )
    stored_cred = cred_result.scalar_one_or_none()

    if not stored_cred:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown credential")

    import webauthn
    try:
        verification = webauthn.verify_authentication_response(
            credential=body.credential,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=settings.WEBAUTHN_ORIGIN,
            credential_public_key=stored_cred.public_key,
            credential_current_sign_count=stored_cred.sign_count,
        )
    except webauthn.helpers.exceptions.InvalidAuthenticationResponse as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Authentication failed: {e}")

    stored_cred.sign_count = verification.new_sign_count
    session.add(stored_cred)

    if stored_cred.user_type == "staff":
        user_result = await session.execute(select(User).where(User.id == stored_cred.user_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
        token = create_access_token(subject=str(user.id), role=user.role, user_type="staff")
        return {"access_token": token, "token_type": "bearer", "role": user.role, "user_type": "staff"}
    else:
        user_result = await session.execute(select(Customer).where(Customer.id == stored_cred.user_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer not found")
        token = create_access_token(subject=str(user.id), role="customer", user_type="customer")
        return {"access_token": token, "token_type": "bearer", "user_type": "customer"}


@router.get("/credentials")
async def list_credentials(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if isinstance(current_user, User):
        user_type, user_id = "staff", current_user.id
    else:
        user_type, user_id = "customer", current_user.id

    result = await session.execute(
        select(WebAuthnCredential).where(
            WebAuthnCredential.user_type == user_type,
            WebAuthnCredential.user_id == user_id,
        )
    )
    credentials = result.scalars().all()
    return [
        WebAuthnCredentialResponse(
            id=c.id,
            name=c.name,
            credential_device_type=c.credential_device_type,
            credential_backed_up=c.credential_backed_up,
            created_at=c.created_at.isoformat() if c.created_at else "",
        )
        for c in credentials
    ]


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_current_user),
):
    if isinstance(current_user, User):
        user_type, user_id = "staff", current_user.id
    else:
        user_type, user_id = "customer", current_user.id

    result = await session.execute(
        select(WebAuthnCredential).where(
            WebAuthnCredential.id == credential_id,
            WebAuthnCredential.user_type == user_type,
            WebAuthnCredential.user_id == user_id,
        )
    )
    cred = result.scalar_one_or_none()
    if cred is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    await session.delete(cred)
    await session.commit()
    return {"detail": "Credential deleted"}
