# Local Development Setup

## Prerequisites

- Python 3.12+
- Neon PostgreSQL account (free)
- Gmail account with App Password

## 1. Clone & Install

```bash
git clone <repo-url> emenu
cd emenu
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

## 2. Environment Variables

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
```

Edit `.env` with your credentials. See [CONFIG.md](CONFIG.md) for all variables.

Minimum required:
- `DATABASE_URL` — Neon PostgreSQL connection string
- `JWT_SECRET` — Random string for JWT signing
- `SMTP_USER` + `SMTP_PASSWORD` — Gmail App Password

## 3. Run the Server

```bash
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## 4. Run Tests

```bash
python -m pytest tests/ -v
```

Tests use SQLite (in-memory) — no external database needed.

## 5. Docker (Optional)

```bash
docker compose up --build
```

## Getting Credentials

### Neon Database
1. Sign up at https://neon.tech
2. Create a project
3. Copy the connection string from the dashboard

### Gmail App Password
1. Enable 2FA on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password
4. Copy the 16-character password

### Cloudinary (for images)
1. Sign up at https://cloudinary.com
2. Copy Cloud Name, API Key, and API Secret from the dashboard

### eSewa (test mode)
- Merchant ID: `EPAYTEST`
- Secret Key: `8gBm/:&EnhH.1/q`
- No signup needed for testing

### Khalti (sandbox)
1. Sign up at https://khalti.com as merchant
2. Get Secret Key from merchant dashboard
