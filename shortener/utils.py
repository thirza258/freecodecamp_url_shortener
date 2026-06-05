from __future__ import annotations

import base64
from io import BytesIO

import qrcode
from django.conf import settings


def build_short_link(short_code: str) -> str:
    return f"{settings.SHORT_LINK_PROTOCOL}://{settings.SHORT_LINK_DOMAIN}/{short_code}"


def build_qr_data_uri(payload: str) -> str:
    qr = qrcode.QRCode(border=2, box_size=8)
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
