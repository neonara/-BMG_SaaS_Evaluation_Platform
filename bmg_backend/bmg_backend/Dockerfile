FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/

# ── production ────────────────────────────────────────────────
FROM base AS production

# CRITICAL: pin production settings — prevents dev middleware bake-in
ENV DJANGO_SETTINGS_MODULE=config.settings.production

RUN pip install -r requirements/production.txt

COPY . .
# Remove dev-only debug files from production image
RUN rm -f middleware_debug.py minimal_test.py test_simple.py wsgi_test.py

RUN chmod +x entrypoint.sh

RUN addgroup --system django \
    && adduser --system --ingroup django django \
    && chown -R django:django /app

USER django
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

# ── development ───────────────────────────────────────────────
FROM base AS development

ENV DJANGO_SETTINGS_MODULE=config.settings.development

RUN pip install -r requirements/dev.txt

COPY . .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ── test ──────────────────────────────────────────────────────
FROM base AS test

ENV DJANGO_SETTINGS_MODULE=config.settings.test

RUN pip install -r requirements/dev.txt

COPY . .
ENTRYPOINT []
CMD ["python", "-m", "pytest", "--tb=short", "-q"]
