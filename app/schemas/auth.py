from typing import Optional

from pydantic import BaseModel


class StaffLoginRequest(BaseModel):
    email: str
    password: str


class CustomerRegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class CustomerLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Optional[str] = None
    user_type: str
    requires_totp: bool = False
    temp_token: Optional[str] = None


class StaffCreateRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class AdminPasswordResetRequest(BaseModel):
    new_password: str


class VerifyTOTPRequest(BaseModel):
    code: str
    temp_token: Optional[str] = None
    remember_device: bool = False


class DisableTOTPRequest(BaseModel):
    code: str
