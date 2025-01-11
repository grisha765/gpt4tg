FROM python:3.12-alpine

RUN apk add --no-cache file gcc musl-dev pango

WORKDIR /app

COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1

ENV DB_PATH="/app/database/gpt4tg.json"

CMD ["python", "main.py"]

