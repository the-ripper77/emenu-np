import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_template(filename: str, **kwargs) -> str:
    path = TEMPLATES_DIR / filename
    html = path.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        html = html.replace("{{" + key + "}}", str(value))
    return html


async def send_email(to: str, subject: str, html: str) -> Optional[str]:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured, skipping email")
        return None

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.EMAIL_FROM or settings.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
        )
        logger.info(f"Email sent to {to}")
        return "sent"
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return None


async def send_otp_email(to: str, code: str, purpose: str = "verify your email") -> Optional[str]:
    html = render_template(
        "otp_email.html",
        purpose=purpose,
        code=code,
        expire_minutes=settings.OTP_EXPIRE_MINUTES,
    )
    return await send_email(to, f"eMenu - Your verification code: {code}", html)


async def send_invoice_email(
    to: str,
    customer_name: str,
    order_id: int,
    items: list[dict],
    subtotal: float,
    discount_amount: float | None,
    delivery_fee: float | None,
    total: float,
    order_type: str,
    payment_method: str,
    payment_status: str,
) -> Optional[str]:
    item_rows = ""
    for item in items:
        item_rows += f"""
            <tr>
                <td style="padding: 12px 0; border-bottom: 1px solid #eee;">{item['name']}</td>
                <td style="padding: 12px 0; border-bottom: 1px solid #eee; text-align: center;">{item['quantity']}</td>
                <td style="padding: 12px 0; border-bottom: 1px solid #eee; text-align: right;">Rs {item['price_at_order']:,.0f}</td>
                <td style="padding: 12px 0; border-bottom: 1px solid #eee; text-align: right;">Rs {item['quantity'] * item['price_at_order']:,.0f}</td>
            </tr>
        """

    discount_row = ""
    if discount_amount and discount_amount > 0:
        discount_row = f"""
            <tr>
                <td colspan="3" style="padding: 8px 0; text-align: right; color: #16a34a;">Discount</td>
                <td style="padding: 8px 0; text-align: right; color: #16a34a;">- Rs {discount_amount:,.0f}</td>
            </tr>
        """

    delivery_row = ""
    if delivery_fee and delivery_fee > 0:
        delivery_row = f"""
            <tr>
                <td colspan="3" style="padding: 8px 0; text-align: right;">Delivery Fee</td>
                <td style="padding: 8px 0; text-align: right;">Rs {delivery_fee:,.0f}</td>
            </tr>
        """

    payment_status_class = "paid" if payment_status == "paid" else "pending" if payment_status == "pending" else "failed"

    html = render_template(
        "invoice_email.html",
        order_id=order_id,
        order_type=order_type.replace("_", " ").title(),
        payment_method=payment_method.replace("_", " ").title(),
        payment_status=payment_status.upper(),
        payment_status_class=payment_status_class,
        item_rows=item_rows,
        discount_row=discount_row,
        delivery_row=delivery_row,
        total=f"{total:,.0f}",
    )
    return await send_email(to, f"eMenu - Invoice for Order #{order_id}", html)


async def send_password_reset_email(to: str, raw_token: str, user_type: str = "staff") -> Optional[str]:
    reset_url = f"{settings.APP_BASE_URL}/reset-password?token={raw_token}"
    html = render_template(
        "password_reset_email.html",
        reset_url=reset_url,
        expire_minutes=settings.RESET_TOKEN_EXPIRE_MINUTES,
    )
    return await send_email(to, "eMenu - Reset Your Password", html)
