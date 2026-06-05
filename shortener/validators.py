from __future__ import annotations

from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


SHORT_CODE_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9_-]+$",
    message="Use only letters, numbers, hyphens, and underscores.",
)


def normalize_short_code(value: str) -> str:
    return value.strip().lower()


def validate_http_https_url(value: str) -> None:
    scheme = urlsplit(value.strip()).scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValidationError("Enter a valid URL that starts with http:// or https://.")
