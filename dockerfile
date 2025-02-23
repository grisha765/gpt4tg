FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

WORKDIR /app

COPY pyproject.toml uv.lock /app

RUN uv sync --no-cache


FROM python:3.12-alpine AS main

RUN apk add --no-cache file pango

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY . /app

ENV PATH="/app/.venv/bin:$PATH"

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

ENV DB_PATH="/app/database/gpt4tg.db"

CMD ["python", "main.py"]

