from __future__ import annotations

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import ShortURL
from .validators import SHORT_CODE_VALIDATOR, normalize_short_code, validate_http_https_url


class ShortURLForm(forms.Form):
    original_url = forms.URLField(
        label="Original URL",
        widget=forms.URLInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "https://www.example.com/very/long/path",
                "autocomplete": "off",
            }
        ),
        help_text="Paste the full destination URL.",
    )
    short_code = forms.CharField(
        label="Custom slug",
        required=False,
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "my-link",
                "autocomplete": "off",
            }
        ),
        help_text="Leave blank to generate a random code.",
    )

    def clean_original_url(self) -> str:
        value = self.cleaned_data["original_url"].strip()
        validate_http_https_url(value)
        return value

    def clean_short_code(self) -> str:
        raw_value = self.cleaned_data.get("short_code", "")
        value = normalize_short_code(raw_value) if raw_value else ""
        if not value:
            return value

        SHORT_CODE_VALIDATOR(value)
        reserved = {item.lower() for item in settings.RESERVED_SHORT_CODES}
        if value in reserved:
            raise ValidationError("This short URL already exists. Please choose another slug.")
        if ShortURL.objects.filter(short_code=value).exists():
            raise ValidationError("This short URL already exists. Please choose another slug.")
        return value
