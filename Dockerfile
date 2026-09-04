# ---- builder: install the package + dependencies into an isolated prefix ----
FROM python:3.12-slim AS builder
WORKDIR /build

COPY pyproject.toml ./
COPY app ./app
COPY scripts ./scripts

RUN pip install --no-cache-dir --prefix=/install .

# ---- runtime: slim image, no build tools, non-root user ----
FROM python:3.12-slim AS runtime
WORKDIR /app

RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /install /usr/local

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
