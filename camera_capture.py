"""Модуль захвата фото с двух USB-камер.

Функции:
  capture_photos() -> list[str]
    Сделать снимки со всех камер. Возвращает список путей к файлам.
  open_camera(index) -> cv2.VideoCapture | None
    Открыть камеру по индексу.
"""

import os
import time
from datetime import datetime

import cv2

CAPTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captures")
CAMERAS = [0, 1]
CAPTURE_DELAY = 2.0
READ_RETRIES = 10
WIDTH, HEIGHT = 1280, 960


def _ensure_dir():
    os.makedirs(CAPTURE_DIR, exist_ok=True)


def fourcc_to_str(fourcc: int) -> str:
    return "".join(chr((fourcc >> (8 * k)) & 0xFF) for k in range(4))


def open_camera(index: int) -> cv2.VideoCapture | None:
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    return cap


def capture_photos() -> list[str]:
    """Сделать снимки со всех камер последовательно (~3 сек на 2 камеры)."""
    _ensure_dir()
    paths = []

    for cam_idx in CAMERAS:
        # открываем камеру
        cap = open_camera(cam_idx)
        if cap is None:
            print(f"[камера {cam_idx}] не открылась")
            continue

        # прогрев — пропускаем первые кадры (USB-шина стабилизируется)
        for _ in range(READ_RETRIES):
            cap.read()

        # основной кадр
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            print(f"[камера {cam_idx}] кадр не прочитан")
            continue

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cam{cam_idx}_{timestamp}.jpg"
        path = os.path.join(CAPTURE_DIR, filename)
        cv2.imwrite(path, frame)
        paths.append(path)
        print(f"[камера {cam_idx}] ok")

        # пауза перед следующей камерой (USB-шина не держит две сразу)
        time.sleep(CAPTURE_DELAY)

    return paths


# для ручного запуска: python camera_capture.py
if __name__ == "__main__":
    result = capture_photos()
    print(f"\nИтого: {len(result)} фото")
