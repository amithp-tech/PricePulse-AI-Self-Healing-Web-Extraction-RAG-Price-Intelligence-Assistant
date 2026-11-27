import os
import smtplib
from email.message import EmailMessage

from schemas import ProductData


def check_and_send_alert(product: ProductData, target_price: float) -> bool:
    if product.price <= 0 or product.price >= target_price:
        return False

    my_email = os.getenv("MY_EMAIL")
    my_password = os.getenv("MY_PASSWORD")
    to_email = os.getenv("TO_EMAIL")
    smtp_host = os.getenv("SMTP_HOST", "smtp.outlook.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not all([my_email, my_password, to_email]):
        return False

    msg = EmailMessage()
    msg["Subject"] = f"PricePulse Alert: {product.title}"
    msg["From"] = my_email
    msg["To"] = to_email
    msg.set_content(
        f"{product.title}\n"
        f"Current Price: {product.currency} {product.price:.2f} (Target: {target_price:.2f})\n"
        f"In Stock: {product.in_stock}\n\n"
        f"URL: {product.url}"
    )

    with smtplib.SMTP(smtp_host, smtp_port) as connection:
        connection.starttls()
        connection.login(my_email, my_password)
        connection.send_message(msg)

    return True
