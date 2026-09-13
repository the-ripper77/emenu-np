from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    DATABASE_URL: str = ""
    POSTGRES_PRISMA_URL: str = ""

    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    ESEWA_MERCHANT_ID: str = ""
    ESEWA_SECRET_KEY: str = ""
    ESEWA_BASE_URL: str = "https://epay.esewa.com.np"

    KHALTI_SECRET_KEY: str = ""
    KHALTI_BASE_URL: str = "https://khalti.com/api/v2"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    OTP_EXPIRE_MINUTES: int = 5
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    WEBAUTHN_RP_ID: str = "localhost"
    WEBAUTHN_RP_NAME: str = "eMenu"
    WEBAUTHN_ORIGIN: str = "http://localhost:8000"

    TOTP_ENCRYPTION_KEY: str = "change-me-generate-with-fernet"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    APP_NAME: str = "eMenu"
    APP_BASE_URL: str = "http://localhost:8000"


settings = Settings()

if not settings.DATABASE_URL and settings.POSTGRES_PRISMA_URL:
    settings.DATABASE_URL = settings.POSTGRES_PRISMA_URL
