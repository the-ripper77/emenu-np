# eMenu — Digital Menu & Ordering System

A FastAPI backend for restaurant digital menus, online ordering, and payment processing.

## Features

- **Menu Management** — Categories, items with images, availability toggle
- **Online Ordering** — Dine-in, takeaway, delivery with scheduling
- **Payment Gateways** — eSewa and Khalti integration with server-side verification
- **Campaigns & Promos** — Percentage/fixed discounts, coupon codes, usage limits
- **Authentication** — Email + password for staff and customers
- **2FA** — TOTP (Google Authenticator) with trusted devices
- **Passkeys** — WebAuthn passwordless login
- **Image Hosting** — Cloudinary with auto-deletion on item removal
- **Email** — Gmail SMTP for OTP, invoices, password resets

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| ORM | SQLModel (SQLAlchemy) |
| Database | PostgreSQL (Neon) |
| Auth | JWT + bcrypt + TOTP + WebAuthn |
| Payments | eSewa ePay v2 + Khalti ePayment v2 |
| Images | Cloudinary |
| Email | Gmail SMTP (aiosmtplib) |
| Deploy | Vercel + Neon |

## Quick Start

```bash
# Clone and setup
git clone <repo-url> emenu
cd emenu
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Configure
copy .env.example .env
# Edit .env with your credentials

# Run
uvicorn app.main:app --reload
```

API docs at: http://localhost:8000/docs

## Documentation

| File | Description |
|------|------------|
| [SETUP.md](SETUP.md) | Local development setup |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Vercel + Neon deployment |
| [API.md](API.md) | All API endpoints |
| [MODELS.md](MODELS.md) | Database models |
| [AUTH.md](AUTH.md) | Authentication flows |
| [PAYMENTS.md](PAYMENTS.md) | Payment gateway integration |
| [CONFIG.md](CONFIG.md) | Environment variables |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Project structure |
