# Nevatal URL Shortener

Production-ready Django URL shortener with server-rendered Bootstrap 5 UI.

## Features

- Shorten long URLs
- Optional custom slugs
- Duplicate slug prevention with database uniqueness and form validation
- Root-path redirects for `https://nevatal.tech/<short_code>`
- Click analytics, last-accessed timestamps, and dashboard stats
- Request rate limiting with friendly 429 responses
- Production Docker deployment with PostgreSQL 16 Alpine and Redis

## Local setup

1. Copy [`.env.example`](/home/thirzq/url_shortener/.env.example) to `.env` and update the values.
2. Build and run the stack:

```bash
docker compose up --build
```

The Django app listens on port `8200`.
PostgreSQL is exposed as the `postgres` service inside the Compose network.
Redis is used for caching and rate limiting through Django's cache layer.

## Deployment

1. Create a production `.env` from [`.env.example`](/home/thirzq/url_shortener/.env.example).
2. Set `SECRET_KEY` to a strong random value.
3. Set `DEBUG=0`.
4. Set `ALLOWED_HOSTS` to the real hostnames for your deployment.
5. Set `POSTGRES_PASSWORD`, `POSTGRES_DB`, and `POSTGRES_USER` to your production database credentials.
6. Set `POSTGRES_HOST=postgres` and `POSTGRES_PORT=5432` when using the provided Compose file.
7. Set `REDIS_URL=redis://redis:6379/1` when using the provided Compose file.
8. Set `DOMAIN_NAME` and `PUBLIC_SHORT_DOMAIN` to the public app and short-link domains.
9. Start the stack with:

```bash
docker compose up --build -d
```

The web container runs Django migrations and static collection on startup.

## Environment

The app expects these variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `REDIS_URL`
- `DOMAIN_NAME`
- `PUBLIC_SHORT_DOMAIN`

The Compose file provides sane defaults for local development:

- Main app domain: `url.nevatal.tech`
- Public short-link domain: `nevatal.tech`

## URL structure

- Main site: `https://url.nevatal.tech`
- Public short links: `https://nevatal.tech/<short_code>`

## Notes

- The project uses Django templates only.
- The app generates secure random 7-10 character codes by default.
- Custom slugs are normalized to lowercase.
