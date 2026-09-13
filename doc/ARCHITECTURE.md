# Architecture

## Project Structure

```
emenu/
├── app/
│   ├── api/                    # API route handlers
│   │   ├── auth.py             # Login, register, password reset
│   │   ├── admin.py            # Staff CRUD, permissions
│   │   ├── categories.py       # Menu categories
│   │   ├── menu_items.py       # Menu items
│   │   ├── restaurant.py       # Restaurant profile
│   │   ├── promo_banners.py    # Promo banners
│   │   ├── campaigns.py        # Discount campaigns
│   │   ├── orders.py           # Order creation, fulfillment
│   │   ├── payments.py         # eSewa/Khalti callbacks
│   │   ├── email.py            # Email verification OTP
│   │   ├── totp.py             # TOTP 2FA endpoints
│   │   └── webauthn.py         # WebAuthn passkey endpoints
│   ├── models/                 # SQLModel table definitions
│   │   ├── user.py             # Staff users
│   │   ├── customer.py         # Customers
│   │   ├── category.py         # Menu categories
│   │   ├── menu_item.py        # Menu items
│   │   ├── order.py            # Orders
│   │   ├── order_item.py       # Order line items
│   │   ├── order_status_history.py
│   │   ├── campaign.py         # Discount campaigns
│   │   ├── promo_banner.py     # Promo banners
│   │   ├── restaurant_profile.py
│   │   ├── permission.py       # Permission keys
│   │   ├── role_permission.py  # Role-permission mapping
│   │   ├── webauthn_credential.py
│   │   ├── webauthn_challenge.py
│   │   ├── trusted_device.py   # TOTP trusted devices
│   │   ├── email_verification.py
│   │   ├── staff_password_reset_token.py
│   │   ├── customer_password_reset_token.py
│   │   └── __init__.py         # All model imports
│   ├── schemas/                # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── menu.py
│   │   ├── restaurant.py
│   │   ├── payment.py
│   │   └── webauthn.py
│   ├── services/               # Business logic
│   │   ├── auth_service.py     # Password hashing, JWT, tokens
│   │   ├── payment_service.py  # eSewa/Khalti API calls
│   │   ├── cloudinary_service.py # Image upload/delete
│   │   └── email_service.py    # SMTP email sending
│   ├── config.py               # Settings (pydantic-settings)
│   ├── database.py             # Async engine, session factory
│   ├── deps.py                 # FastAPI dependencies (auth)
│   └── main.py                 # App entry, lifespan, routers
├── tests/                      # Pytest test suite
│   ├── conftest.py             # Fixtures, test DB setup
│   ├── test_auth.py
│   ├── test_menu.py
│   ├── test_campaigns.py
│   └── test_orders.py
├── doc/                        # Documentation
├── alembic/                    # Database migrations (empty)
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | FastAPI | Async Python web framework |
| ORM | SQLModel | SQLAlchemy + Pydantic |
| Database | PostgreSQL (Neon) | Production database |
| Auth | JWT + bcrypt | Password hashing + tokens |
| 2FA | pyotp | TOTP (Google Authenticator) |
| Passkeys | webauthn | WebAuthn FIDO2 |
| Payments | eSewa + Khalti | Nepali payment gateways |
| Images | Cloudinary | Image hosting + CDN |
| Email | aiosmtplib | Async Gmail SMTP |
| Testing | pytest + httpx | Async test suite |
| Deploy | Vercel | Serverless deployment |

## Request Flow

```
Client Request
    ↓
FastAPI Router (api/*.py)
    ↓
Dependencies (deps.py)
  - get_session → DB session
  - require_current_user → JWT decode
  - require_permission() → Role check
    ↓
Route Handler
    ↓
Service Layer (services/*.py)
    ↓
Database (SQLModel/SQLAlchemy)
    ↓
Response (JSON)
```

## Authentication Layers

```
1. JWT Token
   └─ Required on all /api/admin/* and protected routes

2. TOTP 2FA (optional)
   └─ Checked after password login
   └─ Trusted devices skip for 30 days

3. WebAuthn Passkeys (optional)
   └─ Alternative to password + TOTP
   └─ Returns JWT directly
```

## Image Lifecycle

```
1. Frontend uploads to Cloudinary directly
2. Frontend receives secure_url
3. Frontend sends URL to backend API
4. Backend stores URL in database
5. On update: old image deleted from Cloudinary
6. On delete: image deleted from Cloudinary
```

## Payment Lifecycle

```
1. Order created → payment_status: "pending"
2. POST /api/payments/initiate → returns gateway form/URL
3. User pays on gateway
4. Gateway redirects to callback URL
5. Backend verifies via gateway API
6. Validates amount matches order
7. Updates payment_status: "paid"
8. Logs in order_status_history
```
