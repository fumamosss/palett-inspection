"""Фоновые задачи (запускаются в потоке через app.run_worker(thread=True)).

Все задачи принимают callable on_update — функцию, которую вызывают в
главном потоке (через app.call_from_thread) для обновления интерфейса.
"""

import os
import time
from datetime import datetime

import cv2

from distance import open_distance, get_distance, close_distance
from camera_capture import open_camera, CAMERAS, CAPTURE_DIR, READ_RETRIES, CAPTURE_DELAY
from llm import analyze_photos
from settings import Settings


def _wait_clear(on_update, get_dist):
    """Ждать, пока перед датчиком никто не стоит."""
    on_update(None, "Ожидание очищения пространства", None)
    while True:
        dist = get_dist()
        if dist is not None and dist > Settings.threshold:
            on_update(dist, "Готов к работе", None)
            return
        time.sleep(0.2)


def distance_loop(on_update, stop):
    """Непрерывно читать дальномер. stop() == True — выход."""
    if not open_distance():
        on_update(None)
        return
    try:
        while not stop():
            on_update(get_distance())
            time.sleep(0.5)
    finally:
        close_distance()


def cameras_capture(on_update):
    """Снять по фото с каждой камеры. on_update(cam_idx, status, detail):
    status: TAKING / SAVED / ERROR."""
    os.makedirs(CAPTURE_DIR, exist_ok=True)

    for cam_idx in CAMERAS:
        on_update(cam_idx, "TAKING", "")

        cap = open_camera(cam_idx)
        if cap is None:
            on_update(cam_idx, "ERROR", "не открылась")
            time.sleep(CAPTURE_DELAY)
            continue

        for _ in range(READ_RETRIES):
            cap.read()
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            on_update(cam_idx, "ERROR", "кадр не прочитан")
            time.sleep(CAPTURE_DELAY)
            continue

        filename = f"cam{cam_idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(CAPTURE_DIR, filename)
        try:
            cv2.imwrite(path, frame)
        except Exception as e:
            on_update(cam_idx, "ERROR", str(e))
            time.sleep(CAPTURE_DELAY)
            continue

        on_update(cam_idx, "SAVED", path)
        time.sleep(CAPTURE_DELAY)


def inspection_loop(on_update, stop):
    """Полный цикл инспекции: дальномер -> фото -> нейронка."""
    threshold = Settings.threshold
    detect_time = Settings.detect_time
    cooldown = Settings.cooldown

    if not open_distance():
        on_update(None, "Дальномер не найден", None)
        return
    try:
        _wait_clear(on_update, get_distance)

        state = "IDLE"
        state_start = time.time()

        while not stop():
            dist = get_distance()
            now = time.time()

            if dist is None:
                time.sleep(0.5)
                continue

            elapsed = now - state_start

            if state == "IDLE":
                if dist <= threshold:
                    state = "DETECT"
                    state_start = now
                    on_update(dist, "DETECT", None)

            elif state == "DETECT":
                if dist > threshold:
                    state = "IDLE"
                    state_start = now
                    on_update(dist, "IDLE", None)
                elif elapsed >= detect_time:
                    on_update(dist, "Съёмка...", None)
                    photos = capture_photos()
                    on_update(dist, "Анализ...", photos)
                    if photos:
                        try:
                            analyze_photos(photos)
                            on_update(dist, "Готово", photos)
                        except Exception as e:
                            on_update(dist, f"Ошибка нейронки: {e}", photos)
                    else:
                        on_update(dist, "Фото не сохранены", None)
                    state = "COOLDOWN"
                    state_start = now

            elif state == "COOLDOWN":
                if dist > threshold and elapsed >= cooldown:
                    state = "IDLE"
                    state_start = now
                    on_update(dist, "IDLE", None)

            time.sleep(0.05)

    finally:
        close_distance()