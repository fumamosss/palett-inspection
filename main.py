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
DETECT_TIME = 1.5         # сек. Объект должен быть ближе порога столько, чтобы считать палетту.
COOLDOWN_TIME = 5.0       # сек. После фотки — объект должен уйти на > порога столько, чтобы ловить новый.

# Состояния
IDLE = "IDLE"
DETECT = "DETECT"
COOLDOWN = "COOLDOWN"


def inspect_pallet():
    """Основной цикл проверки с debounce."""
    print(f"Порог: {DISTANCE_THRESHOLD} мм | Детект: {DETECT_TIME}с | Кулдаун: {COOLDOWN_TIME}с")
    print("Инициализация дальномера...")

    if not open_distance():
        print("Дальномер не найден. Проверьте подключение.")
        return
    print("Дальномер готов.")

    # Ждём, пока перед датчиком никто не стоит (дистанция > порога)
    print("Ожидание очищения пространства...", end="", flush=True)
    while True:
        dist = get_distance()
        if dist is not None and dist > DISTANCE_THRESHOLD:
            print(f" OK ({dist} мм)")
            break
        print(".", end="", flush=True)
        time.sleep(0.2)

    state = IDLE
    state_start = time.time()
    print()

    try:
        while True:
            dist = get_distance()
            now = time.time()

            if dist is None:
                time.sleep(0.05)
                continue

            elapsed = now - state_start

            if state == IDLE:
                if dist <= DISTANCE_THRESHOLD:
                    # Объект появился — запоминаем время, переходим в DETECT
                    state = DETECT
                    state_start = now
                    print(f"[IDLE→DETECT] объект на {dist} мм")
                # иначе — стоим в IDLE, ждём

            elif state == DETECT:
                if dist > DISTANCE_THRESHOLD:
                    # Объект пропал до детекта — отмена
                    state = IDLE
                    state_start = now
                    print(f"[DETECT→IDLE] объект пропал ({dist} мм)")
                elif elapsed >= DETECT_TIME:
                    # Объект держался достаточно долго — фоткаем!
                    print(f"[DETECT] палетта подтверждена ({dist} мм) — снимаем")
                    photos = capture_photos()
                    if photos:
                        print(f"  Сохранены: {photos}")
                    else:
                        print("  Фото не сохранены")
                    state = COOLDOWN
                    state_start = now
                    print(f"[DETECT→COOLDOWN] кулдаун {COOLDOWN_TIME}с")

            elif state == COOLDOWN:
                if dist > DISTANCE_THRESHOLD and elapsed >= COOLDOWN_TIME:
                    # Объект ушёл достаточно долго — готовы ловить новый
                    state = IDLE
                    state_start = now
                    print(f"[COOLDOWN→IDLE] готов к новой палетте")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nОстановка.")
    finally:
        close_distance()


if __name__ == "__main__":
    inspect_pallet()
