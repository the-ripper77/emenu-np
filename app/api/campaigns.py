from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.database import get_session
from app.deps import CurrentAdmin
from app.models.campaign import Campaign
from app.models.order import Order
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignValidateRequest

router = APIRouter(tags=["campaigns"])


@router.get("/api/admin/campaigns")
async def list_campaigns(session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(Campaign).order_by(Campaign.id))
    campaigns = result.scalars().all()

    output = []
    for c in campaigns:
        count_result = await session.execute(
            select(func.count(Order.id)).where(Order.campaign_id == c.id)
        )
        usage_count = count_result.scalar() or 0
        output.append({**c.model_dump(), "usage_count": usage_count})

    return output


@router.post("/api/admin/campaigns")
async def create_campaign(body: CampaignCreate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    if body.code:
        existing = await session.execute(select(Campaign).where(Campaign.code == body.code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Campaign code already exists")

    campaign = Campaign(**body.model_dump())
    session.add(campaign)
    await session.commit()
    await session.refresh(campaign)
    return campaign


@router.put("/api/admin/campaigns/{campaign_id}")
async def update_campaign(campaign_id: int, body: CampaignUpdate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)

    session.add(campaign)
    await session.commit()
    return campaign


@router.delete("/api/admin/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: int, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    await session.delete(campaign)
    await session.commit()
    return {"detail": "Deleted"}


@router.post("/api/campaigns/validate")
async def validate_campaign(body: CampaignValidateRequest, session: AsyncSession = Depends(get_session)):
    import datetime

    result = await session.execute(select(Campaign).where(Campaign.code == body.code, Campaign.is_active == True))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid campaign code")

    today = datetime.date.today()
    if campaign.start_date and today < campaign.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign not yet active")
    if campaign.end_date and today > campaign.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign has expired")

    if campaign.min_order_amount and body.order_total < campaign.min_order_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum order amount is {campaign.min_order_amount}",
        )

    if campaign.usage_limit_total:
        count_result = await session.execute(
            select(func.count(Order.id)).where(Order.campaign_id == campaign.id)
        )
        if (count_result.scalar() or 0) >= campaign.usage_limit_total:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign usage limit reached")

    if campaign.usage_limit_per_customer and body.customer_id:
        count_result = await session.execute(
            select(func.count(Order.id)).where(
                Order.campaign_id == campaign.id, Order.customer_id == body.customer_id
            )
        )
        if (count_result.scalar() or 0) >= campaign.usage_limit_per_customer:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already used this campaign")

    if campaign.discount_type == "percentage":
        discount = body.order_total * (float(campaign.discount_value) / 100)
        if campaign.max_discount_amount:
            discount = min(discount, float(campaign.max_discount_amount))
    else:
        discount = float(campaign.discount_value)

    discount = min(discount, body.order_total)

    return {
        "campaign_id": campaign.id,
        "name": campaign.name,
        "discount_type": campaign.discount_type,
        "discount_amount": round(discount, 2),
    }


@router.get("/api/campaigns/available")
async def available_campaigns(
    session: AsyncSession = Depends(get_session),
    order_total: float = 0,
):
    import datetime

    today = datetime.date.today()
    result = await session.execute(
        select(Campaign).where(
            Campaign.is_active == True,
            Campaign.code.is_(None),
            (Campaign.start_date.is_(None) | (Campaign.start_date <= today)),
            (Campaign.end_date.is_(None) | (Campaign.end_date >= today)),
        )
    )
    campaigns = result.scalars().all()

    available = []
    for c in campaigns:
        if c.min_order_amount and order_total < c.min_order_amount:
            continue
        if c.discount_type == "percentage":
            discount = order_total * (float(c.discount_value) / 100)
            if c.max_discount_amount:
                discount = min(discount, float(c.max_discount_amount))
        else:
            discount = float(c.discount_value)
        discount = min(discount, order_total)
        available.append({"id": c.id, "name": c.name, "discount_amount": round(discount, 2)})

    return available
