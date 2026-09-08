"""Точка входа: TUI-меню + операции.

Запуск:  python main.py

Меню возвращает код запускаемого действия через app.exit(код):
  - "inspect"    -> inspect_pallet(): цикл проверки с debounce
  - "dist_test"  -> run_distance_test(): показать расстояние в реальном времени
  - "cam_test"   -> run_camera_test(): снять по фото со всех камер
  - None         -> просто выход

Настройки берутся из settings.Settings (файл settings.json).
"""

import time

from settings import Settings
from distance import open_distance, get_distance, close_distance
from camera_capture import capture_photos
from llm import analyze_photos

# Состояния
IDLE = "IDLE"
DETECT = "DETECT"
COOLDOWN = "COOLDOWN"


def inspect_pallet():
    """Основной цикл проверки с debounce."""
    threshold = Settings.threshold
    detect_time = Settings.detect_time
    cooldown = Settings.cooldown

    print(f"Порог: {threshold} см | Детект: {detect_time}с | Кулдаун: {cooldown}с")
    print("Инициализация дальномера...")

    if not open_distance():
        print("Дальномер не найден. Проверьте подключение.")
        return
    print("Дальномер готов.")

    # Ждём, пока перед датчиком никто не стоит (дистанция > порога)
    print("Ожидание очищения пространства...", end="", flush=True)
    while True:
        dist = get_distance()
        if dist is not None and dist > threshold:
            print(f" OK ({dist})")
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
                time.sleep(0.5)
                continue

            elapsed = now - state_start

            if state == IDLE:
                if dist <= threshold:
                    # Объект появился — запоминаем время, переходим в DETECT
                    state = DETECT
                    state_start = now
                    print(f"[IDLE→DETECT] объект на {dist} см")
                # иначе — стоим в IDLE, ждём

            elif state == DETECT:
                if dist > threshold:
                    # Объект пропал до детекта — отмена
                    state = IDLE
                    state_start = now
                    print(f"[DETECT→IDLE] объект пропал ({dist} см)")
                elif elapsed >= detect_time:
                    # Объект держался достаточно долго — фоткаем!
                    print(f"[DETECT] палетта подтверждена ({dist} см) — снимаем")
                    photos = capture_photos()
                    if photos:
                        print(f"  Сохранены: {photos}")
                        # Отправка в нейронку
                        try:
                            result = analyze_photos(photos)
                            print(f"  Анализ: {result}")
                        except Exception as e:
                            print(f"  Ошибка нейронки: {e}")
                    else:
                        print("  Фото не сохранены")
                    state = COOLDOWN
                    state_start = now
                    print(f"[DETECT→COOLDOWN] кулдаун {cooldown}с")

            elif state == COOLDOWN:
                if dist > threshold and elapsed >= cooldown:
                    # Объект ушёл достаточно долго — готовы ловить новый
                    state = IDLE
                    state_start = now
                    print(f"[COOLDOWN→IDLE] готов к новой палетте")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nОстановка.")
    finally:
        close_distance()


def run_distance_test():
    """Показать расстояние с дальномера в реальном времени. Ctrl+C — выход."""
    print("Инициализация дальномера...")
    if not open_distance():
        print("Дальномер не найден. Проверьте подключение.")
        return
    print("Дальномер готов. Ctrl+C — выход.\n")

    try:
        while True:
            dist = get_distance()
            if dist is None:
                print("нет данных")
            else:
                print(f"расстояние: {dist} см")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nОстановка.")
    finally:
        close_distance()


def run_camera_test():
    """Снять по одному фото с каждой камеры и показать пути."""
    print("Съёмка фото...")
    photos = capture_photos()
    if photos:
        print(f"Сохранены: {photos}")
    else:
        print("Фото не сохранены")


def run_action(action):
    """Запустить выбранное в меню действие."""
    if action == "inspect":
        inspect_pallet()
    elif action == "dist_test":
        run_distance_test()
    elif action == "cam_test":
        run_camera_test()


def main():
    from menu import MenuApp

    run_action(MenuApp().run())


if __name__ == "__main__":
    main()