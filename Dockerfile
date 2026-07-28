# syntax=docker/dockerfile:1

FROM node:20-alpine AS frontend-build
WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-fund --no-audit

COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    STATIC_DIR=/app/static

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
COPY backend /app/backend
COPY scripts /app/scripts
COPY config /app/config
COPY infra/docker-entrypoint.sh /app/infra/docker-entrypoint.sh
COPY infra/docker-worker-entrypoint.sh /app/infra/docker-worker-entrypoint.sh

RUN pip install .

COPY --from=frontend-build /frontend/dist /app/static

RUN sed -i 's/\r$//' /app/infra/docker-entrypoint.sh /app/infra/docker-worker-entrypoint.sh \
    && chmod +x /app/infra/docker-entrypoint.sh /app/infra/docker-worker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)"

ENTRYPOINT ["/app/infra/docker-entrypoint.sh"]
