FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock /app

RUN uv sync --no-cache


FROM python:3.12-slim-bookworm AS main

RUN apt-get update && apt-get install -y libcairo2 file libpango-1.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY . /app

ENV PATH="/app/.venv/bin:$PATH"

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

ENV DB_PATH="/app/database/gpt4tg.db"

CMD ["python", "main.py"]

