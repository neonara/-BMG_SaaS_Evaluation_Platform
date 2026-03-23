# syntax=docker/dockerfile:1

# syntax=docker/dockerfile:1

# Builder: install all deps
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements/ requirements/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    -r requirements/base.txt \
    -r requirements/dev.txt \
    -r requirements/production.txt \
    -r requirements/test.txt

# Production runtime (used by docker-compose target:production)
FROM python:3.12-slim AS production
# Install runtime deps: libpq (psycopg2), libjpeg/geos (Pillow), curl/tini (health/PID1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tini libpq-dev gcc g++ libpq5 \
    libjpeg62-turbo libwebp7 libtiff6 liblcms2-2 \
    libgeos-dev libproj-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
WORKDIR /app
COPY . .
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app /usr/local/lib/python3.12 /usr/local/bin
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--worker-class", "gthread", \
    "--threads", "2", \
    "--timeout", "120", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]

# Development stage (mount source)
FROM python:3.12-slim AS development
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl vim libpq-dev gcc && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements/ requirements/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements/dev.txt
COPY . .
USER appuser
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
