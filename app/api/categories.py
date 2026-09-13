from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.deps import CurrentAdmin
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.schemas.menu import CategoryCreate, CategoryUpdate

router = APIRouter(tags=["categories"])


@router.get("/api/categories")
async def list_categories(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Category).order_by(Category.sort_order, Category.id))
    categories = result.scalars().all()
    return categories


@router.get("/api/categories/{category_id}")
async def get_category(category_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.post("/api/admin/categories")
async def create_category(body: CategoryCreate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    category = Category(name=body.name, sort_order=body.sort_order)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


@router.put("/api/admin/categories/{category_id}")
async def update_category(category_id: int, body: CategoryUpdate, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if body.name is not None:
        category.name = body.name
    if body.sort_order is not None:
        category.sort_order = body.sort_order

    session.add(category)
    await session.commit()
    return category


@router.delete("/api/admin/categories/{category_id}")
async def delete_category(category_id: int, session: AsyncSession = Depends(get_session), _admin: CurrentAdmin = None):
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    await session.delete(category)
    await session.commit()
    return {"detail": "Deleted"}
