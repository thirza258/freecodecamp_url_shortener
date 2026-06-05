FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=nevatal_url_shortener.settings

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --upgrade pip \
    && pip install --no-index --find-links=/wheels /wheels/*

COPY . /app/

RUN chmod +x /app/scripts/entrypoint.sh

EXPOSE 8200

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["gunicorn", "nevatal_url_shortener.wsgi:application", "--bind", "0.0.0.0:8200", "--workers", "3", "--timeout", "60"]
