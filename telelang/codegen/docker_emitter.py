"""Генератор Docker-окружения для проектов TeleLang."""

from __future__ import annotations
from pathlib import Path


class DockerEmitter:
    """Генерирует Dockerfile, docker-compose.yml и .dockerignore для проекта TeleLang."""

    @classmethod
    def emit(cls, project_dir: Path, project_name: str, is_userbot: bool = False) -> tuple[Path, Path, Path]:
        """Генерирует файлы Docker в директории проекта."""
        dockerfile_path = project_dir / "Dockerfile"
        compose_path = project_dir / "docker-compose.yml"
        dockerignore_path = project_dir / ".dockerignore"

        # 1. Dockerfile
        clean_name = project_name.lower().replace("-", "_").replace(" ", "_")
        extra_pkgs = " telethon>=1.30.0" if is_userbot else ""

        dockerfile_content = f"""# Dockerfile для проекта TeleLang ({project_name})
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir aiogram>=3.0.0 aiosqlite>=0.19.0 python-dotenv>=1.0.0 aiohttp>=3.8.0{extra_pkgs}

# Запуск проекта через встроенный CLI TeleLang
CMD ["python", "-m", "telelang.cli.main", "run", "."]
"""
        dockerfile_path.write_text(dockerfile_content, encoding="utf-8")

        # 2. docker-compose.yml
        compose_content = f"""version: "3.8"

services:
  {clean_name}_bot:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {clean_name}_container
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./database:/app/database
      - ./sessions:/app/sessions
    environment:
      - PYTHONUNBUFFERED=1
"""
        compose_path.write_text(compose_content, encoding="utf-8")

        # 3. .dockerignore
        dockerignore_content = """__pycache__/
*.py[cod]
*$py.class
.git/
.gitignore
.env.local
.venv/
venv/
*.log
.DS_Store
"""
        dockerignore_path.write_text(dockerignore_content, encoding="utf-8")

        return dockerfile_path, compose_path, dockerignore_path
