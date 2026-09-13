from typing import Optional

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    name: str
    code: Optional[str] = None
    discount_type: str
    discount_value: float
    max_discount_amount: Optional[float] = None
    min_order_amount: Optional[float] = None
    usage_limit_total: Optional[int] = None
    usage_limit_per_customer: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    max_discount_amount: Optional[float] = None
    min_order_amount: Optional[float] = None
    usage_limit_total: Optional[int] = None
    usage_limit_per_customer: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: Optional[bool] = None


class CampaignValidateRequest(BaseModel):
    code: str
    order_total: float
    customer_id: Optional[int] = None
