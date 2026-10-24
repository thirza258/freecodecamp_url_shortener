"""Seed the database with demo links and click events so the site looks active.

Usage:
    python manage.py seed_demo            # ~45 links + derived click events
    python manage.py seed_demo --links 20 # a smaller batch

Safe to run repeatedly: vanity slugs that already exist are skipped.
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models import Case, DateTimeField, F, Sum, Value, When
from django.utils import timezone

from shortener.models import ClickEvent, ShortURL

# Vanity slugs -> real, well-known destinations. The demo user owns these.
VANITY_LINKS = [
    ("launch", "https://www.youtube.com/watch?v=aircAruvnKk"),
    ("docs", "https://docs.djangoproject.com/en/5.0/"),
    ("blog", "https://vercel.com/blog"),
    ("gh", "https://github.com/django/django"),
    ("tools", "https://coolors.co/palettes/trending"),
    ("podcast", "https://www.bbc.com/news/technology"),
    ("roadmap", "https://developer.mozilla.org/en-US/docs/Web/JavaScript"),
    ("design", "https://www.figma.com/community"),
    ("jobs", "https://www.meetup.com/"),
    ("status", "https://news.ycombinator.com/"),
]

DESTINATIONS = [
    "https://github.com/django/django",
    "https://docs.djangoproject.com/en/5.0/topics/forms/",
    "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/302",
    "https://news.ycombinator.com/",
    "https://fastapi.tiangolo.com/",
    "https://python-poetry.org/docs/",
    "https://www.docker.com/blog/announcing-docker-compose-v2/",
    "https://www.reddit.com/r/selfhosted/",
    "https://vercel.com/blog",
    "https://tailwindcss.com/docs",
    "https://react.dev/learn",
    "https://kubernetes.io/docs/tutorials/",
    "https://www.postgresql.org/docs/current/index.html",
    "https://redis.io/docs/latest/",
    "https://linuxserver.io/",
    "https://www.figma.com/community",
    "https://stackoverflow.com/questions/11227809/why-is-processing-a-sorted-array-faster-than-processing-an-unsorted-array",
    "https://nodejs.org/en/blog",
    "https://pnpm.io/",
    "https://code.visualstudio.com/download",
    "https://git-scm.com/book/en/v2",
    "https://12factor.net/",
    "https://martinfowler.com/articles/microservices.html",
    "https://ocw.mit.edu/",
    "https://www.khanacademy.org/computing",
    "https://www.eff.org/deeplinks",
    "https://proton.me/blog",
    "https://arstechnica.com/",
    "https://www.bbc.com/news/technology",
    "https://techcrunch.com/",
    "https://www.theverge.com/",
    "https://en.wikipedia.org/wiki/URL_shortening",
    "https://www.notion.so/templates",
    "https://obsidian.md/",
    "https://linear.app/",
    "http://neverssl.com/",
    "https://httpbin.org/",
    "https://caniuse.com/",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Android 14; Mobile; rv:127.0) Gecko/127.0 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    "curl/8.5.0",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Discordbot/2.0",
]

REFERERS = [
    "",
    "",
    "https://www.google.com/",
    "https://www.google.com/search?q=django+url+shortener",
    "https://x.com/",
    "https://twitter.com/",
    "https://www.linkedin.com/",
    "https://www.reddit.com/",
    "https://news.ycombinator.com/",
    "https://t.co/",
    "https://chatgpt.com/",
    "https://github.com/",
]

# Documentation IP ranges (TEST-NET-3, TEST-NET-2, TEST-NET-1) plus doc IPv6.
IPS = [f"203.0.113.{n}" for n in range(1, 60)]
IPS += [f"198.51.100.{n}" for n in range(1, 40)]
IPS += [f"192.0.2.{n}" for n in range(1, 30)]
IPS += ["2001:db8::1", "2001:db8::2", "2001:db8::3", "2001:db8::a", "2001:db8::b"]

DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@nevatal.id"
DEMO_PASSWORD = "DemoPass#2026"


def pick_click_count(rng: random.Random) -> int:
    """Weighted click counts: a few heavy hitters, mostly small, some zero."""
    roll = rng.random()
    if roll < 0.12:  # heavy hitters
        return rng.randint(800, 4200)
    if roll < 0.42:  # medium
        return rng.randint(80, 600)
    if roll < 0.80:  # small
        return rng.randint(3, 60)
    if roll < 0.92:  # barely used
        return rng.randint(1, 2)
    return 0


def random_dt(rng: random.Random, start: float, end: float):
    """Aware datetime between `start` and `end` hours ago."""
    now = timezone.now()
    return now - timedelta(seconds=rng.uniform(start * 3600, end * 3600))


class Command(BaseCommand):
    help = "Seed demo links and click events so the site looks active."

    def add_arguments(self, parser):
        parser.add_argument(
            "--links",
            type=int,
            default=45,
            help="Number of random links to create on top of the vanity links (default: 45).",
        )

    def handle(self, *args, **options):
        rng = random.Random(20260906)
        User = get_user_model()
        now = timezone.now()

        demo_user, created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={"email": DEMO_EMAIL},
        )
        if created:
            demo_user.set_password(DEMO_PASSWORD)
            demo_user.save()
            self.stdout.write(f"Created demo user '{DEMO_USERNAME}' (password: {DEMO_PASSWORD})")
        else:
            self.stdout.write(f"Demo user '{DEMO_USERNAME}' already exists, reusing it.")

        links_created = 0
        vanity_created = 0
        skipped = 0

        def build_link(destination: str, *, short_code: str | None, owner, created_ts, last_accessed_ts, click_count: int, is_active: bool) -> bool:
            """Create one link via the manager, then backdate timestamps and clicks."""
            nonlocal links_created, vanity_created, skipped
            try:
                short_url = ShortURL.objects.create_short_url(
                    original_url=destination,
                    short_code=short_code,
                    owner=owner,
                )
            except IntegrityError:
                skipped += 1
                return False
            # update() bypasses auto_now_add, so we can backdate.
            ShortURL.objects.filter(pk=short_url.pk).update(
                created_at=created_ts,
                last_accessed_at=last_accessed_ts,
                click_count=click_count,
                is_active=is_active,
            )
            if short_code:
                vanity_created += 1
            links_created += 1
            return True

        # 1) Vanity links, owned by the demo user.
        for slug, destination in VANITY_LINKS:
            click_count = pick_click_count(rng)
            created_ts = random_dt(rng, 24 * 14, 24 * 120)  # 2 weeks .. 4 months ago
            last_accessed_ts = random_dt(rng, 0.5, 24 * 3) if click_count else None
            build_link(
                destination,
                short_code=slug,
                owner=demo_user,
                created_ts=created_ts,
                last_accessed_ts=last_accessed_ts,
                click_count=click_count,
                is_active=True,
            )

        # 2) Random links, a mix of anonymous and demo-owned.
        for i in range(options["links"]):
            destination = DESTINATIONS[i % len(DESTINATIONS)]
            click_count = pick_click_count(rng)
            created_ts = random_dt(rng, 1, 24 * 120)
            last_accessed_ts = random_dt(rng, 0.5, 24 * 14) if click_count else None
            owner = demo_user if i < 8 else None  # a few more owned by demo
            is_active = rng.random() > 0.06  # a handful of inactive links
            build_link(
                destination,
                short_code=None,
                owner=owner,
                created_ts=created_ts,
                last_accessed_ts=last_accessed_ts,
                click_count=click_count,
                is_active=is_active,
            )

        # 3) Click events spread over the last 14 days, weighted by click count.
        #    bulk_create runs pre_save, and auto_now_add clobbers the timestamp on
        #    each instance, so keep intended timestamps in a parallel list and
        #    backdate them afterwards with batched CASE updates.
        events = []
        timestamps = []
        for short_url in ShortURL.objects.filter(click_count__gt=0, is_active=True):
            count = min(short_url.click_count, 25)
            for _ in range(count):
                events.append(
                    ClickEvent(
                        short_url=short_url,
                        user_agent=rng.choice(USER_AGENTS),
                        referer=rng.choice(REFERERS),
                        ip_address=rng.choice(IPS) if rng.random() > 0.05 else None,
                    )
                )
                timestamps.append(random_dt(rng, 0.05, 24 * 14))
        ClickEvent.objects.bulk_create(events)

        chunk = 100
        for i in range(0, len(events), chunk):
            batch = list(zip(events[i : i + chunk], timestamps[i : i + chunk]))
            cases = [
                When(pk=event.pk, then=Value(ts, output_field=DateTimeField()))
                for event, ts in batch
            ]
            ClickEvent.objects.filter(pk__in=[event.pk for event, _ in batch]).update(
                timestamp=Case(*cases, default=F("timestamp"))
            )

        total_links = ShortURL.objects.count()
        total_clicks = ShortURL.objects.aggregate(total=Sum("click_count"))["total"]

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
        self.stdout.write(
            f"Links: +{links_created} ({vanity_created} vanity, {skipped} skipped as existing) -> "
            f"{total_links} total"
        )
        self.stdout.write(f"Click events: +{len(events)} -> {ClickEvent.objects.count()} total")
        self.stdout.write(f"Aggregate clicks: {total_clicks or 0}")
        self.stdout.write(f"Latest activity: {ClickEvent.objects.order_by('-timestamp').first().timestamp:%Y-%m-%d %H:%M:%S UTC}")
