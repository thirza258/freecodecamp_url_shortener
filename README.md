# Nevatal URL Shortener

Production-ready Django URL shortener with server-rendered Bootstrap 5 UI.

## Features

- Shorten long URLs
- Optional custom slugs
- Duplicate slug prevention with database uniqueness and form validation
- Root-path redirects for `https://url.nevatal.id/<short_code>`
- Click analytics, last-accessed timestamps, and dashboard stats
- Request rate limiting with friendly 429 responses
- Production Docker deployment with PostgreSQL 16 Alpine and Redis

## Local setup

1. Copy [`.env.example`](/home/thirzq/url_shortener/.env.example) to `.env` and update the values.
2. Build and run the stack:

```bash
docker compose up --build -d
docker compose logs -f web
```

Always run with `-d` (detached): without it the stack stops as soon as the
terminal or SSH session closes.

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

## Keeping it running

Every service has `restart: unless-stopped`, so a crashed container (e.g.
killed by the OOM killer) comes back on its own. Two more steps make the
site survive reboots and logouts:

1. Start the stack detached (see above) — never `docker compose up` in the
   foreground of an SSH session, because closing that session stops it.
2. Optional: install the included systemd unit so systemd starts the stack
   at boot and you never have to think about it:

```bash
# edit WorkingDirectory inside the unit file to point at this repo
sudo cp deploy/nevatal-url-shortener.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nevatal-url-shortener
```

Check on it anytime with `systemctl status nevatal-url-shortener` and
`docker compose logs -f web`.

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
- `FRAME_ANCESTORS` — who may embed the site in an iframe; `*` (default) = any site, a comma-separated origin list to restrict, `none` to block

The Compose file provides sane defaults for local development:

- Main app domain: `url.nevatal.id`
- Public short-link domain: `url.nevatal.id`

## URL structure

- Main site: `https://url.nevatal.id`
- Public short links: `https://url.nevatal.id/<short_code>`

## Notes

- The project uses Django templates only.
- The app generates secure random 7-10 character codes by default.
- Custom slugs are normalized to lowercase.
