from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, async_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    from sqlmodel import SQLModel, select

    if engine is not None:
        from app.models import (
            Campaign,
            Category,
            Customer,
            EmailVerification,
            MenuItem,
            Order,
            OrderItem,
            OrderStatusHistory,
            Permission,
            PromoBanner,
            RestaurantProfile,
            RolePermission,
            User,
            WebAuthnCredential,
            WebAuthnChallenge,
            TrustedDevice,
        )

        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        SEED_PERMISSIONS = [
            ("view_payment_status", "View payment status on orders"),
            ("verify_payment", "Confirm cash/QR payments as received"),
            ("complete_cash_order", "Mark cash orders as completed"),
            ("update_fulfillment_status", "Update order fulfillment status (preparing, ready, etc.)"),
            ("override_gateway_payment", "Override gateway payment status manually"),
            ("edit_menu", "Create, edit, and delete menu categories and items"),
            ("manage_promos", "Create, edit, and delete promo banners and campaigns"),
            ("manage_staff", "Create, edit, and deactivate staff accounts and permissions"),
        ]

        async with async_session() as session:
            for key, description in SEED_PERMISSIONS:
                result = await session.execute(select(Permission).where(Permission.key == key))
                if result.scalar_one_or_none() is None:
                    session.add(Permission(key=key, description=description))
            await session.commit()

    yield

    if engine is not None:
        await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.campaigns import router as campaigns_router
from app.api.categories import router as categories_router
from app.api.email import router as email_router
from app.api.menu_items import router as menu_items_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.promo_banners import router as promo_banners_router
from app.api.restaurant import router as restaurant_router
from app.api.webauthn import router as webauthn_router
from app.api.totp import router as totp_router

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(email_router)
app.include_router(categories_router)
app.include_router(menu_items_router)
app.include_router(restaurant_router)
app.include_router(promo_banners_router)
app.include_router(campaigns_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(webauthn_router)
app.include_router(totp_router)


@app.get("/")
async def root():
    return {"message": "eMenu API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
