# Authentication Guide

## Overview

eMenu supports multiple authentication methods:

| Method | Who | How |
|--------|-----|-----|
| Email + Password | Staff & Customers | Standard login |
| TOTP 2FA | Staff & Customers | Google Authenticator |
| WebAuthn Passkeys | Staff & Customers | Biometric/device login |
| Password Reset | Staff & Customers | Email link |

---

## Staff Login Flow

```
1. POST /api/auth/login
   { "email": "staff@example.com", "password": "pass123" }

2a. If TOTP NOT enabled:
    → Returns { "access_token": "...", "role": "staff" }

2b. If TOTP enabled AND device NOT trusted:
    → Returns { "requires_totp": true, "temp_token": "..." }

3. POST /api/totp/verify-login
   { "code": "123456", "temp_token": "...", "remember_device": true }

4. Returns { "access_token": "...", "trusted_token": "..." }
```

## Customer Registration & Login

```
1. POST /api/auth/customer/register
   { "email": "customer@example.com", "password": "pass123", "name": "John" }

   → Returns { "access_token": "...", "user_type": "customer" }

2. POST /api/auth/customer/login
   { "email": "customer@example.com", "password": "pass123" }

   → Same TOTP flow as staff if enabled
```

## Password Reset Flow

### Staff
```
1. POST /api/auth/forgot-password
   { "email": "staff@example.com" }
   → Email sent with reset link

2. User clicks link → redirected to reset page

3. POST /api/auth/reset-password
   { "token": "<from_url>", "new_password": "newpass123" }
   → Password updated
```

### Customer
```
1. POST /api/auth/customer/forgot-password
   { "email": "customer@example.com" }

2. POST /api/auth/customer/reset-password
   { "token": "<from_url>", "new_password": "newpass123" }
```

---

## TOTP 2FA Setup

### Step 1: Generate Secret
```
POST /api/totp/setup
Authorization: Bearer <token>

Response:
{
  "secret": "JBSWY3DPEHPK3PXP",
  "provisioning_uri": "otpauth://totp/eMenu:user@example.com?secret=...",
  "qr_code": "data:image/png;base64,..."
}
```

### Step 2: Scan QR Code
Open Google Authenticator → scan the QR code.

### Step 3: Verify & Enable
```
POST /api/totp/verify
Authorization: Bearer <token>
Body: { "code": "123456" }

Response: { "detail": "TOTP enabled successfully" }
```

### Trusted Devices
When `remember_device: true` is set during login, a 30-day trusted token is issued.
Subsequent logins skip TOTP if the trusted token is sent via `X-Trusted-Token` header.

---

## WebAuthn Passkeys

### Registration
```
1. POST /api/webauthn/register/begin
   Body: { "email": "user@example.com", "user_type": "customer" }
   → Returns WebAuthn registration options

2. Browser prompts for biometric/device auth

3. POST /api/webauthn/register/finish
   Body: { "email": "...", "user_type": "customer", "credential": {...} }
   → Passkey saved
```

### Authentication
```
1. POST /api/webauthn/authenticate/begin
   Body: { "email": "user@example.com", "user_type": "customer" }
   → Returns WebAuthn authentication options

2. Browser prompts for biometric/device auth

3. POST /api/webauthn/authenticate/finish
   Body: { "credential": {...} }
   → Returns { "access_token": "...", "user_type": "customer" }
```

---

## JWT Token Structure

```json
{
  "sub": "1",
  "role": "admin",
  "type": "staff",
  "exp": 1234567890
}
```

- `sub`: User ID
- `role`: User role (for staff) or `"customer"`
- `type`: `"staff"` or `"customer"`
- `exp`: Expiration timestamp

Default expiry: 30 minutes (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`).
