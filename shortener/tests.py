from __future__ import annotations

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse

from .models import ClickEvent, ShortURL


class BaseShortenerTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()
        super().tearDown()


class ShortenerIndexTests(BaseShortenerTestCase):
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

    def test_guest_creation_does_not_attach_an_owner(self) -> None:
        response = self.client.post(
            reverse("index"),
            data={
                "original_url": "https://example.com/guest",
                "short_code": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        short_url = ShortURL.objects.latest("created_at")
        self.assertIsNone(short_url.owner)


class ShortenerAuthTests(BaseShortenerTestCase):
    def test_registers_and_signs_in_user_without_email(self) -> None:
        response = self.client.post(
            reverse("register"),
            data={
                "username": "alice",
                "password1": "strong-pass-12345",
                "password2": "strong-pass-12345",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard"))
        self.assertTrue(get_user_model().objects.filter(username="alice").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_logged_in_user_can_create_owned_urls(self) -> None:
        user = get_user_model().objects.create_user(username="bob", password="strong-pass-12345")
        self.client.login(username="bob", password="strong-pass-12345")

        response = self.client.post(
            reverse("index"),
            data={
                "original_url": "https://example.com/owned",
                "short_code": "owned-link",
            },
        )

        self.assertEqual(response.status_code, 302)
        short_url = ShortURL.objects.get(short_code="owned-link")
        self.assertEqual(short_url.owner, user)

    def test_dashboard_contains_personal_links_for_authenticated_users(self) -> None:
        user = get_user_model().objects.create_user(username="carol", password="strong-pass-12345")
        ShortURL.objects.create(original_url="https://example.com/owned", short_code="carol-link", owner=user)
        self.client.login(username="carol", password="strong-pass-12345")

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "carol-link")
        self.assertContains(response, "Your links")


class ShortenerRedirectTests(BaseShortenerTestCase):
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
        self.assertContains(response, "https://url.nevatal.tech/success123")
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

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 429)
        self.assertContains(second, "Too many requests", status_code=429)


class ShortenerSEOTests(BaseShortenerTestCase):
    def test_landing_page_renders_seo_tags_and_schema(self) -> None:
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

        # Title & Meta description
        self.assertContains(response, "<title>Nevatal URL Shortener — Fast, Secure &amp; Modern URL Shortener</title>")
        self.assertContains(response, '<meta name="description"')
        self.assertContains(response, '<meta name="keywords"')
        self.assertContains(response, '<link rel="canonical"')

        # Open Graph & Twitter
        self.assertContains(response, '<meta property="og:title"')
        self.assertContains(response, '<meta property="og:description"')
        self.assertContains(response, '<meta property="og:image"')
        self.assertContains(response, '<meta name="twitter:card" content="summary_large_image">')

        # Favicons & Manifest
        self.assertContains(response, 'rel="icon"')
        self.assertContains(response, 'favicon.')
        self.assertContains(response, '/site.webmanifest')

        # Structured Data Schema
        self.assertContains(response, '"@type": "WebApplication"')
        self.assertContains(response, '"@type": "FAQPage"')

        # Sections
        self.assertContains(response, 'id="features"')
        self.assertContains(response, 'id="how-it-works"')
        self.assertContains(response, 'id="use-cases"')
        self.assertContains(response, 'id="faq"')

    def test_robots_txt_endpoint(self) -> None:
        response = self.client.get(reverse("robots_txt"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response["Content-Type"])
        self.assertContains(response, "User-agent: *")
        self.assertContains(response, "Disallow: /admin/")
        self.assertContains(response, "Sitemap:")

    def test_sitemap_xml_endpoint(self) -> None:
        response = self.client.get(reverse("sitemap_xml"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response["Content-Type"])
        self.assertContains(response, "<urlset")
        self.assertContains(response, "<loc>")

    def test_site_manifest_endpoint(self) -> None:
        response = self.client.get(reverse("site_manifest"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["name"], "Nevatal URL Shortener")
        self.assertEqual(data["short_name"], "Nevatal")

    def test_reserved_slugs_include_seo_endpoints(self) -> None:
        from django.conf import settings
        self.assertIn("robots.txt", settings.RESERVED_SHORT_CODES)
        self.assertIn("sitemap.xml", settings.RESERVED_SHORT_CODES)
        self.assertIn("site.webmanifest", settings.RESERVED_SHORT_CODES)
        self.assertIn("favicon.svg", settings.RESERVED_SHORT_CODES)
