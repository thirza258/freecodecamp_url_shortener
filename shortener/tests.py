from __future__ import annotations

from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse

from .models import ClickEvent, ShortURL


class ShortenerIndexTests(TestCase):
    def test_create_custom_slug(self) -> None:
        response = self.client.post(
            reverse("index"),
            data={
                "original_url": "https://www.example.com/very/long/path",
                "short_code": "My-Link",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("success", kwargs={"short_code": "my-link"}))
        self.assertTrue(ShortURL.objects.filter(short_code="my-link", original_url="https://www.example.com/very/long/path").exists())

    def test_duplicate_slug_shows_user_friendly_error(self) -> None:
        ShortURL.objects.create(original_url="https://example.com/one", short_code="my-link")

        response = self.client.post(
            reverse("index"),
            data={
                "original_url": "https://example.com/two",
                "short_code": "my-link",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This short URL already exists. Please choose another slug.")

    def test_rejects_disallowed_url_schemes(self) -> None:
        for bad_url in ("javascript:alert(1)", "data:text/plain,hello", "file:///etc/passwd"):
            response = self.client.post(
                reverse("index"),
                data={
                    "original_url": bad_url,
                    "short_code": "safe-link",
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Enter a valid URL that starts with http:// or https://.")

    def test_manager_rejects_disallowed_url_schemes(self) -> None:
        with self.assertRaises(ValidationError):
            ShortURL.objects.create_short_url(
                original_url="javascript:alert(1)",
                short_code="safe-link",
            )

    def test_manager_normalizes_custom_slug(self) -> None:
        short_url = ShortURL.objects.create_short_url(
            original_url="https://example.com/one",
            short_code="  My-Link  ",
        )

        self.assertEqual(short_url.short_code, "my-link")

    def test_generated_slug_is_secure_random_alphanumeric_and_in_length_range(self) -> None:
        response = self.client.post(
            reverse("index"),
            data={
                "original_url": "https://www.example.com/very/long/path",
                "short_code": "",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/success/"))
        short_url = ShortURL.objects.latest("created_at")
        self.assertRegex(short_url.short_code, r"^[A-Za-z0-9]+$")
        self.assertGreaterEqual(len(short_url.short_code), 7)
        self.assertLessEqual(len(short_url.short_code), 10)

    def test_generated_slug_retries_on_collision(self) -> None:
        ShortURL.objects.create(original_url="https://example.com/one", short_code="DUPLICATE")

        with patch.object(ShortURL.objects, "generate_short_code", side_effect=["DUPLICATE", "UNIQUE123"]):
            short_url = ShortURL.objects.create_short_url(original_url="https://example.com/two")

        self.assertEqual(short_url.short_code, "UNIQUE123")


class ShortenerRedirectTests(TestCase):
    def test_redirects_existing_short_code(self) -> None:
        ShortURL.objects.create(original_url="https://www.example.com/landing", short_code="AbC123xY")

        response = self.client.get("/AbC123xY")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://www.example.com/landing")
        self.assertEqual(ShortURL.objects.get(short_code="AbC123xY").click_count, 1)
        self.assertIsNotNone(ShortURL.objects.get(short_code="AbC123xY").last_accessed_at)
        self.assertTrue(ClickEvent.objects.filter(short_url__short_code="AbC123xY").exists())

    def test_unknown_short_code_returns_404(self) -> None:
        response = self.client.get("/does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "This link does not exist.", status_code=404)

    def test_success_page_shows_short_link_and_qr_code(self) -> None:
        ShortURL.objects.create(original_url="https://www.example.com/landing", short_code="success123")

        response = self.client.get(reverse("success", kwargs={"short_code": "success123"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "https://nevatal.tech/success123")
        self.assertContains(response, "data:image/png;base64,")

    @override_settings(SHORTENER_REDIRECT_RATE_LIMIT="1/m")
    def test_redirect_rate_limit_returns_429(self) -> None:
        ShortURL.objects.create(original_url="https://www.example.com/landing", short_code="RateLimit1")

        first = self.client.get("/RateLimit1")
        second = self.client.get("/RateLimit1")

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 429)
        self.assertContains(second, "Too many requests", status_code=429)

    @override_settings(SHORTENER_CREATE_RATE_LIMIT="1/m")
    def test_creation_rate_limit_returns_429(self) -> None:
        first = self.client.post(
            reverse("index"),
            data={
                "original_url": "https://example.com/one",
                "short_code": "",
            },
        )
        second = self.client.post(
            reverse("index"),
            data={
                "original_url": "https://example.com/two",
                "short_code": "",
            },
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertContains(second, "Too many requests", status_code=429)
