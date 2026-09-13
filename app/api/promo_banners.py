from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.deps import CurrentAdmin
from app.models.promo_banner import PromoBanner
from app.schemas.restaurant import PromoBannerCreate, PromoBannerUpdate
from app.services.cloudinary_service import delete_image

router = APIRouter(tags=["promo-banners"])


@router.get("/api/promo-banners")
async def list_promo_banners(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(PromoBanner)
        .where(PromoBanner.is_active == True)
        .order_by(PromoBanner.sort_order, PromoBanner.id)
    )
    return result.scalars().all()


@router.post("/api/admin/promo-banners")
async def create_promo_banner(body: PromoBannerCreate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    banner = PromoBanner(**body.model_dump())
    session.add(banner)
    await session.commit()
    await session.refresh(banner)
    return banner


@router.put("/api/admin/promo-banners/{banner_id}")
async def update_promo_banner(banner_id: int, body: PromoBannerUpdate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(PromoBanner).where(PromoBanner.id == banner_id))
    banner = result.scalar_one_or_none()
    if banner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner not found")

    update_data = body.model_dump(exclude_unset=True)
    if "image_url" in update_data and banner.image_url and update_data["image_url"] != banner.image_url:
        delete_image(banner.image_url)

    for field, value in update_data.items():
        setattr(banner, field, value)

    session.add(banner)
    await session.commit()
    return banner


@router.delete("/api/admin/promo-banners/{banner_id}")
async def delete_promo_banner(banner_id: int, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(PromoBanner).where(PromoBanner.id == banner_id))
    banner = result.scalar_one_or_none()
    if banner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner not found")

    if banner.image_url:
        delete_image(banner.image_url)

    await session.delete(banner)
    await session.commit()
    return {"detail": "Deleted"}
