from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    yield

    from app.database import engine
    if engine is not None:
        await engine.dispose()


app = FastAPI(title="EMENU NP", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "eMenu API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
