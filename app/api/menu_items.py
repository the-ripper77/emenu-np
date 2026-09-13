from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.deps import CurrentAdmin
from app.models.menu_item import MenuItem
from app.schemas.menu import MenuItemCreate, MenuItemUpdate
from app.services.cloudinary_service import delete_image

router = APIRouter(tags=["menu-items"])


@router.get("/api/menu-items")
async def list_menu_items(
    session: AsyncSession = Depends(get_session),
    category_id: int | None = Query(None),
    available_only: bool = Query(True),
):
    query = select(MenuItem).order_by(MenuItem.sort_order, MenuItem.id)
    if category_id is not None:
        query = query.where(MenuItem.category_id == category_id)
    if available_only:
        query = query.where(MenuItem.is_available == True)
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/api/menu-items/{item_id}")
async def get_menu_item(item_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    return item


@router.post("/api/admin/menu-items")
async def create_menu_item(body: MenuItemCreate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    item = MenuItem(
        category_id=body.category_id,
        name=body.name,
        description=body.description,
        price=body.price,
        image_url=body.image_url,
        is_available=body.is_available,
        sort_order=body.sort_order,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put("/api/admin/menu-items/{item_id}")
async def update_menu_item(item_id: int, body: MenuItemUpdate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")

    update_data = body.model_dump(exclude_unset=True)
    if "image_url" in update_data and item.image_url and update_data["image_url"] != item.image_url:
        delete_image(item.image_url)

    for field, value in update_data.items():
        setattr(item, field, value)

    session.add(item)
    await session.commit()
    return item


@router.delete("/api/admin/menu-items/{item_id}")
async def delete_menu_item(item_id: int, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")

    if item.image_url:
        delete_image(item.image_url)

    await session.delete(item)
    await session.commit()
    return {"detail": "Deleted"}
