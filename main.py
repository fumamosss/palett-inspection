"""Основная логика проверки палетты.

Использует:
  - distance.py — дальномер VL53L1X
  - camera_capture.py — захват фото с двух камер
"""

import time

from distance import open_distance, get_distance, close_distance
from camera_capture import capture_photos

# Порог расстояния (мм). Если дальномер показывает меньше — палетта наклонена.
DISTANCE_THRESHOLD = 1000


def inspect_pallet():
    """Основной цикл проверки."""
    print("Инициализация дальномера...")
    if not open_distance():
        print("Дальномер не найден. Проверьте подключение.")
        return
    print("Дальномер готов.\n")

    try:
        while True:
            dist = get_distance()

            if dist is not None and dist < DISTANCE_THRESHOLD:
                # Палетта близко / наклонена — нужна проверка
                print(f"Обнаружено расстояние {dist} мм (ниже порога {DISTANCE_THRESHOLD})")

                # --- Здесь выполняется логика анализа ---
                # TODO: определение угла наклона палетты
                # TODO: анализ обёртки плёнкой
                # TODO: решение о необходимости вмешательства

                # Захват фото для документации / отправки в нейронку
                photos = capture_photos()
                if photos:
                    print(f"Сохранены фото: {photos}")

                    # TODO: отправка фото в LLM для оценки наклона
                    # TODO: анализ ответа нейронки
                    # TODO: логирование результата

                print()

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\nОстановка.")
    finally:
        close_distance()


if __name__ == "__main__":
    inspect_pallet()
