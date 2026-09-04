"""Основная логика проверки палетты.

Логика:
  - Дальномер следит за расстоянием.
  - Когда объект появляется (расстояние падает ниже порога) — камеры делают снимок.
  - Одно фото за одно появление (не спамит).

Запуск:  python main.py
Выход:   Ctrl+C
"""

import time

from distance import open_distance, get_distance, close_distance
from camera_capture import capture_photos

# ============================================
# НАСТРОЙКИ
# ============================================
DISTANCE_THRESHOLD = 800  # мм. Если <= этого значения — объект перед датчиком.
COOLDOWN = 3.0            # сек. Пауза между срабатываниями (чтобы не фоткать 100 раз).


def inspect_pallet():
    """Основной цикл проверки."""
    print(f"Порог расстояния: {DISTANCE_THRESHOLD} мм")
    print(f"Кулдаун: {COOLDOWN} сек")
    print("Инициализация дальномера...")

    if not open_distance():
        print("Дальномер не найден. Проверьте подключение.")
        return
    print("Дальномер готов.\n")

    last_capture_time = 0
    try:
        while True:
            dist = get_distance()

            if dist is None:
                time.sleep(0.05)
                continue

            now = time.time()

            if dist <= DISTANCE_THRESHOLD and (now - last_capture_time) > COOLDOWN:
                # Объект перед датчиком — фоткаем
                print(f"Объект обнаружен: {dist} мм")
                photos = capture_photos()
                if photos:
                    print(f"  Сохранены: {photos}")
                else:
                    print("  Фото не сохранены")
                last_capture_time = now

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nОстановка.")
    finally:
        close_distance()


if __name__ == "__main__":
    inspect_pallet()
