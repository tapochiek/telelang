"""Модуль горячей перезагрузки (Hot-Reload) для tele dev."""

from __future__ import annotations
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
from telelang.compiler import TeleCompiler
from telelang.errors import TeleLangError


class DevWatcher:
    """Отслеживает изменения .tl-файлов и автоматически перезапускает бота."""

    def __init__(self, file_path: str | Path, cli_token: Optional[str] = None):
        self.file_path = Path(file_path).resolve()
        self.cli_token = cli_token
        self.process: Optional[subprocess.Popen] = None
        self.watch_dir = self.file_path.parent
        self._last_mtimes: dict[Path, float] = {}

    def get_tracked_files(self) -> list[Path]:
        """Возвращает список всех .tl и .env файлов в директории проекта."""
        tracked = []
        if self.file_path.exists():
            tracked.append(self.file_path)

        for p in self.watch_dir.glob("*.tl"):
            if p not in tracked:
                tracked.append(p)

        env_file = self.watch_dir / ".env"
        if env_file.exists() and env_file not in tracked:
            tracked.append(env_file)

        return tracked

    def check_for_changes(self) -> bool:
        """Проверяет, изменился ли хотя бы один отслеживаемый файл."""
        files = self.get_tracked_files()
        changed = False

        for f in files:
            try:
                mtime = f.stat().st_mtime
                if f not in self._last_mtimes:
                    self._last_mtimes[f] = mtime
                elif mtime > self._last_mtimes[f]:
                    self._last_mtimes[f] = mtime
                    changed = True
            except OSError:
                pass

        return changed

    def start_bot_process(self) -> None:
        """Запускает процесс бота."""
        self.stop_bot_process()

        # Предварительная быстрая проверка синтаксиса перед запуском
        try:
            TeleCompiler.compile_file(self.file_path)
        except TeleLangError as e:
            print(f"\n[DEV] Ошибка в коде. Ожидание исправлений...\n", file=sys.stderr)
            print(e.format_report(), file=sys.stderr)
            return

        print(f"\n[DEV] Запуск бота '{self.file_path.name}'...")
        cmd = [sys.executable, "-m", "telelang.cli.main", "run", str(self.file_path)]
        if self.cli_token:
            cmd.extend(["--token", self.cli_token])

        self.process = subprocess.Popen(cmd)

    def stop_bot_process(self) -> None:
        """Останавливает процесс бота."""
        if self.process and self.process.poll() is None:
            print("[DEV] Перезапуск процесса...")
            self.process.terminate()
            try:
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def watch(self) -> None:
        """Главный цикл отслеживания изменений (hot-reload)."""
        print(f"[DEV] Режим разработки активен. Отслеживание: '{self.watch_dir}'")
        print("[DEV] Для выхода нажмите Ctrl+C.\n")

        # Инициализация mtime
        self.check_for_changes()
        self.start_bot_process()

        try:
            while True:
                time.sleep(0.5)
                if self.check_for_changes():
                    print(f"\n[DEV] Обнаружено изменение файла. Перезапуск...")
                    self.start_bot_process()
        except KeyboardInterrupt:
            print("\n[DEV] Остановка режима разработки...")
            self.stop_bot_process()
