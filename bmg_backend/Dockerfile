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
# Install runtime deps...
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tini libpq-dev gcc g++ libpq5 \
    libjpeg62-turbo libwebp7 libtiff6 liblcms2-2 \
    libgeos-dev libproj-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
WORKDIR /app
COPY . .

# Create appuser first, then create and set ownership for directories
RUN adduser --disabled-password --gecos '' appuser && \
    mkdir -p /app/staticfiles && \
    chown -R appuser:appuser /app /usr/local/lib/python3.12 /usr/local/bin

USER appuser

# Development stage (mount source)
FROM python:3.12-slim AS development
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl vim libpq-dev gcc && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements/ requirements/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements/dev.txt
COPY . .
RUN adduser --disabled-password --gecos '' appuser  
USER appuser
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
