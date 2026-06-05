from __future__ import annotations

import secrets
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction

from .validators import SHORT_CODE_VALIDATOR, normalize_short_code, validate_http_https_url


class ShortURLManager(models.Manager):
    alphabet = string.ascii_letters + string.digits

    def generate_short_code(self, length: int | None = None) -> str:
        if length is None:
            length = secrets.randbelow(settings.SHORT_CODE_LENGTH_MAX - settings.SHORT_CODE_LENGTH_MIN + 1) + settings.SHORT_CODE_LENGTH_MIN
        return "".join(secrets.choice(self.alphabet) for _ in range(length))

    def short_code_exists(self, short_code: str) -> bool:
        return self.filter(short_code=short_code).exists() or short_code.lower() in settings.RESERVED_SHORT_CODES

    def create_short_url(
        self,
        *,
        original_url: str,
        short_code: str | None = None,
        owner: models.Model | None = None,
    ) -> "ShortURL":
        original_url = original_url.strip()
        if short_code:
            short_code = normalize_short_code(short_code)
            if self.short_code_exists(short_code):
                raise IntegrityError("Short code already exists.")
            short_url = self.model(original_url=original_url, short_code=short_code, owner=owner)
            short_url.full_clean(validate_unique=False)
            with transaction.atomic():
                return self.create(
                    original_url=short_url.original_url,
                    short_code=short_url.short_code,
                    owner=short_url.owner,
                )

        max_attempts = 50
        for _ in range(max_attempts):
            candidate = self.generate_short_code()
            if self.short_code_exists(candidate):
                continue
            short_url = self.model(original_url=original_url, short_code=candidate, owner=owner)
            short_url.full_clean(validate_unique=False)
            try:
                with transaction.atomic():
                    return self.create(
                        original_url=short_url.original_url,
                        short_code=short_url.short_code,
                        owner=short_url.owner,
                    )
            except IntegrityError:
                continue
        raise IntegrityError("Unable to generate a unique short code.")


class ShortURL(models.Model):
    original_url = models.URLField(max_length=2048, validators=[validate_http_https_url])
    short_code = models.CharField(max_length=50, unique=True, db_index=True, validators=[SHORT_CODE_VALIDATOR])
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="short_urls",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    click_count = models.PositiveIntegerField(default=0, db_index=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    objects = ShortURLManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-click_count", "-created_at"], name="shorturl_popular_idx"),
            models.Index(fields=["-created_at"], name="shorturl_recent_idx"),
            models.Index(fields=["-last_accessed_at"], name="shorturl_accessed_idx"),
            models.Index(fields=["is_active"], name="shorturl_active_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.short_code} -> {self.original_url}"

    def clean(self) -> None:
        super().clean()
        if self.original_url:
            try:
                validate_http_https_url(self.original_url)
            except ValidationError as exc:
                raise ValidationError({"original_url": exc.messages[0]}) from exc
        if self.short_code and self.short_code.lower() in settings.RESERVED_SHORT_CODES:
            raise ValidationError({"short_code": "This short URL already exists. Please choose another slug."})


class ClickEvent(models.Model):
    short_url = models.ForeignKey(ShortURL, on_delete=models.CASCADE, related_name="click_events")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True)
    referer = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["short_url", "-timestamp"], name="clickevent_short_ts_idx"),
            models.Index(fields=["-timestamp"], name="clickevent_ts_idx"),
            models.Index(fields=["ip_address", "-timestamp"], name="clickevent_ip_ts_idx"),
        ]

    def __str__(self) -> str:
        return f"Click event for {self.short_url.short_code} at {self.timestamp.isoformat()}"
