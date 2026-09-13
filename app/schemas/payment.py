from pydantic import BaseModel


class PaymentInitiateRequest(BaseModel):
    order_id: int
    provider: str


class PaymentInitiateResponse(BaseModel):
    provider: str
    redirect_url: str | None = None
    payment_url: str | None = None
    form_data: dict | None = None
