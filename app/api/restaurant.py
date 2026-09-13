from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.deps import CurrentAdmin
from app.models.restaurant_profile import RestaurantProfile
from app.schemas.restaurant import RestaurantProfileUpdate
from app.services.cloudinary_service import delete_image

router = APIRouter(tags=["restaurant-profile"])


@router.get("/api/restaurant-profile")
async def get_restaurant_profile(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(RestaurantProfile).limit(1))
    profile = result.scalar_one_or_none()
    if profile is None:
        return {"name": "", "description": "", "address": "", "phone": "", "opening_hours": ""}
    return profile


@router.put("/api/admin/restaurant-profile")
async def update_restaurant_profile(body: RestaurantProfileUpdate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(RestaurantProfile).limit(1))
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = RestaurantProfile(**body.model_dump(exclude_unset=True))
        session.add(profile)
    else:
        update_data = body.model_dump(exclude_unset=True)
        if "logo_url" in update_data and profile.logo_url and update_data["logo_url"] != profile.logo_url:
            delete_image(profile.logo_url)

        for field, value in update_data.items():
            setattr(profile, field, value)
        session.add(profile)

    await session.commit()
    await session.refresh(profile)
    return profile
