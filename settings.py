"""Хранение настроек приложения.

Настройки лежат в файле settings.json рядом с exe (или рядом со скриптом,
если запускаем python-ом).

Функции:
  Settings.load()  — прочитать настройки из файла (при старте программы).
  Settings.save()  — записать текущие настройки в файл (после изменения).
  Settings.reset() — вернуть значения по умолчанию и сохранить.
"""

import json
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Запущены как exe (PyInstaller): sys.executable указывает на сам exe
    BASE_DIR = Path(sys.executable).parent
else:
    # Запущены как обычный скрипт (python main.py): папка скрипта
    BASE_DIR = Path(__file__).parent

SETTINGS_FILE = BASE_DIR / "settings.json"


class Settings:
    # Значения по умолчанию (для сброса)
    DEFAULTS = {
        "threshold": 50,     # см. Объект ближе этого порога = он на стенде
        "detect_time": 1.5,  # сек. Столько объект должен стоять, чтобы считать палетту
        "cooldown": 2.0,     # сек. Столько стенд должен пустовать после анализа
    }

    # Текущие значения (инициализируются дефолтами, load() обновляет их)
    threshold = DEFAULTS["threshold"]
    detect_time = DEFAULTS["detect_time"]
    cooldown = DEFAULTS["cooldown"]

    @classmethod
    def load(cls):
        """Прочитать настройки из settings.json.

        Если файла нет или он битый — остаются текущие (т.е. дефолтные) значения.
        """
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return
        for key, default in cls.DEFAULTS.items():
            value = data.get(key, default)
            try:
                setattr(cls, key, type(default)(value))
            except (TypeError, ValueError):
                setattr(cls, key, default)

    @classmethod
    def save(cls):
        """Записать текущие настройки в settings.json."""
        data = {key: getattr(cls, key) for key in cls.DEFAULTS}
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def reset(cls):
        """Вернуть значения по умолчанию и сохранить их."""
        for key, default in cls.DEFAULTS.items():
            setattr(cls, key, default)
        cls.save()