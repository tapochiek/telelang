# Dockerfile для проекта TeleLang (modular_bot)
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir aiogram>=3.0.0 aiosqlite>=0.19.0 python-dotenv>=1.0.0 aiohttp>=3.8.0

# Запуск проекта через встроенный CLI TeleLang
CMD ["python", "-m", "telelang.cli.main", "run", "."]
