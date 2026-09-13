# Environment Variables

Copy `.env.example` to `.env` and fill in your values.

---

## Required

### Database
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (async) | `postgresql+asyncpg://user:pass@host/db` |

### JWT
| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | Secret key for JWT signing | `change-me` |
| `JWT_ALGORITHM` | Signing algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |

---

## Services

### Cloudinary (Image Hosting)
| Variable | Description |
|----------|-------------|
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | API key |
| `CLOUDINARY_API_SECRET` | API secret |

### eSewa (Payment Gateway)
| Variable | Description | Default |
|----------|-------------|---------|
| `ESEWA_MERCHANT_ID` | Merchant code | `EPAYTEST` (sandbox) |
| `ESEWA_SECRET_KEY` | HMAC signing key | `8gBm/:&EnhH.1/q` (sandbox) |
| `ESEWA_BASE_URL` | API base URL | `https://epay.esewa.com.np` |

Production: `https://epay.esewa.com.np`
UAT: `https://rc-epay.esewa.com.np`

### Khalti (Payment Gateway)
| Variable | Description | Default |
|----------|-------------|---------|
| `KHALTI_SECRET_KEY` | API key from dashboard | |
| `KHALTI_BASE_URL` | API base URL | `https://khalti.com/api/v2` |

Sandbox: `https://dev.khalti.com/api/v2`
Production: `https://khalti.com/api/v2`

### Gmail SMTP (Email)
| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | Gmail address | |
| `SMTP_PASSWORD` | Gmail App Password | |
| `EMAIL_FROM` | Sender display | |

Get App Password: https://myaccount.google.com/apppasswords

---

## WebAuthn (Passkeys)
| Variable | Description | Default |
|----------|-------------|---------|
| `WEBAUTHN_RP_ID` | Relying party ID (your domain) | `localhost` |
| `WEBAUTHN_RP_NAME` | Display name | `eMenu` |
| `WEBAUTHN_ORIGIN` | Expected origin URL | `http://localhost:8000` |

For production, set these to your domain:
```
WEBAUTHN_RP_ID=emenu.vercel.app
WEBAUTHN_ORIGIN=https://emenu.vercel.app
```

---

## App
| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `eMenu` |
| `APP_BASE_URL` | Public URL | `http://localhost:8000` |

---

## Optional (Unused)
| Variable | Description |
|----------|-------------|
| `TOTP_ENCRYPTION_KEY` | Reserved for future TOTP secret encryption |
| `GOOGLE_CLIENT_ID` | Reserved for future Google OAuth |
| `GOOGLE_CLIENT_SECRET` | Reserved for future Google OAuth |

---

## Minimum for Local Dev

```dotenv
DATABASE_URL=postgresql+asyncpg://neondb_owner:pass@ep-xxx.neon.tech/neondb?sslmode=require
JWT_SECRET=any-random-string
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_FROM=eMenu <your_email@gmail.com>
```

All other variables have sensible defaults or are optional.
