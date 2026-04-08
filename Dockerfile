# ---------- builder ----------
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml .
COPY fertility_sense/ fertility_sense/
COPY cards/ cards/
COPY data/ data/

RUN pip install --no-cache-dir --prefix=/install ".[feeds]"

# ---------- runtime ----------
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

COPY --from=builder /install /usr/local
COPY --from=builder /build/fertility_sense /app/fertility_sense
COPY --from=builder /build/cards /app/cards
COPY --from=builder /build/data /app/data
COPY pyproject.toml /app/

WORKDIR /app

RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9300/health || exit 1

EXPOSE 9300

CMD ["uvicorn", "fertility_sense.api:app", "--host", "0.0.0.0", "--port", "9300"]
