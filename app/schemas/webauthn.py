from typing import Optional

from pydantic import BaseModel


class WebAuthnRegisterBeginRequest(BaseModel):
    email: str
    user_type: str = "customer"


class WebAuthnRegisterFinishRequest(BaseModel):
    email: str
    user_type: str = "customer"
    credential: dict


class WebAuthnAuthBeginRequest(BaseModel):
    email: Optional[str] = None
    user_type: str = "customer"


class WebAuthnAuthFinishRequest(BaseModel):
    credential: dict


class WebAuthnCredentialResponse(BaseModel):
    id: int
    name: Optional[str]
    credential_device_type: Optional[str]
    credential_backed_up: bool
    created_at: str
