from typing import Optional

from pydantic import BaseModel


class DayHours(BaseModel):
    open: str
    close: str


class RestaurantProfileUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    business_hours: Optional[dict[str, Optional[DayHours]]] = None


class PromoBannerCreate(BaseModel):
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_type: str = "none"
    link_target_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class PromoBannerUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_type: Optional[str] = None
    link_target_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
