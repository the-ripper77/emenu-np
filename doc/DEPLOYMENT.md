# Deployment Guide

## Vercel Deployment

### 1. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Import to Vercel

1. Go to https://vercel.com
2. Click **Add New → Project**
3. Import your GitHub repository
4. Vercel auto-detects Python — framework preset: **Other**

### 3. Environment Variables

Go to **Settings → Environment Variables** and add:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Neon connection string (with `+asyncpg`) |
| `JWT_SECRET` | Random string (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Your Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Your Cloudinary API secret |
| `ESEWA_MERCHANT_ID` | Your eSewa merchant ID |
| `ESEWA_SECRET_KEY` | Your eSewa secret key |
| `ESEWA_BASE_URL` | `https://epay.esewa.com.np` (production) |
| `KHALTI_SECRET_KEY` | Your Khalti secret key |
| `KHALTI_BASE_URL` | `https://khalti.com/api/v2` (production) |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | Your Gmail App Password |
| `EMAIL_FROM` | `eMenu <your_email@gmail.com>` |
| `WEBAUTHN_RP_ID` | Your domain (e.g., `emenu.vercel.app`) |
| `WEBAUTHN_RP_NAME` | `eMenu` |
| `WEBAUTHN_ORIGIN` | `https://emenu.vercel.app` |
| `APP_NAME` | `eMenu` |
| `APP_BASE_URL` | `https://emenu.vercel.app` |

### 4. Deploy

Click **Deploy**. Vercel builds and deploys automatically.

### 5. Custom Domain (Optional)

1. Go to **Settings → Domains**
2. Add your domain
3. Update `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGIN`, and `APP_BASE_URL` to match

## Production Checklist

- [ ] Change `ESEWA_BASE_URL` to `https://epay.esewa.com.np`
- [ ] Change `KHALTI_BASE_URL` to `https://khalti.com/api/v2`
- [ ] Set `JWT_SECRET` to a strong random string
- [ ] Set `WEBAUTHN_RP_ID` to your production domain
- [ ] Set `WEBAUTHN_ORIGIN` to `https://your-domain.com`
- [ ] Set `APP_BASE_URL` to `https://your-domain.com`
- [ ] Enable Neon connection pooling (already default)

## Database

Tables are created automatically on first startup via `SQLModel.metadata.create_all`. No manual migration needed for initial setup.

For schema changes later, use Alembic:
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```
