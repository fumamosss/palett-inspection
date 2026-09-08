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
    status: TAKING / SAVED / ERROR. Возвращает список сохранённых путей."""
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    paths = []

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
        paths.append(path)
        time.sleep(CAPTURE_DELAY)

    return paths


def inspection_loop(on_status, on_distance, on_camera, on_result, stop):
    """Полный цикл инспекции: дальномер -> фото -> нейронка.

    Колбэки (вызываются для UI):
      on_status(state_key, started_at) — состояние инспекции
      on_distance(dist)                — текущая дистанция
      on_camera(cam_idx, status, detail) — статус камеры (TAKING/SAVED/ERROR)
      on_result(result | None, error | None) — результат ИИ или текст ошибки
    """
    threshold = Settings.threshold
    detect_time = Settings.detect_time
    cooldown = Settings.cooldown
    START_TIMEOUT = 2.0  # сек. сколько показывать "Объект пропал" перед ожиданием

    if not open_distance():
        on_result(None, "Дальномер не найден")
        return
    try:
        state = "WAIT"
        state_start = time.time()
        on_status("WAIT", None)
        last_dist_sent = 0.0

        while not stop():
            dist = get_distance()
            now = time.time()

            if now - last_dist_sent >= 0.2:
                last_dist_sent = now
                on_distance(dist)

            if dist is None:
                time.sleep(0.05)
                continue

            elapsed = now - state_start

            if state == "WAIT":
                if dist <= threshold:
                    state = "FOUND"
                    state_start = now
                    on_status("FOUND", state_start)

            elif state == "FOUND":
                if dist > threshold:
                    # объект исчез до подтверждения
                    state = "LOST"
                    state_start = now
                    on_status("LOST", None)
                elif elapsed >= detect_time:
                    # объект держался достаточно долго. Снимаем синхронно;
                    # блокирующий захват держит "Фиксируем" на экране.
                    state = "FIX"
                    state_start = now
                    on_status("FIX", None)
                    photos = cameras_capture(on_camera)
                    if not photos:
                        on_result(None, "Фото не сохранены")
                        state = "DONE"
                        state_start = time.time()
                        on_status("DONE", None)
                    else:
                        state = "ANALYZING"
                        state_start = time.time()
                        on_status("ANALYZING", state_start)
                        on_result(None, None)  # сигнал: анализ начался (спиннер)
                        try:
                            result = analyze_photos(photos)
                            on_result(result, None)
                        except Exception as e:
                            on_result(None, str(e))
                        state = "DONE"
                        state_start = time.time()
                        on_status("DONE", None)

            elif state == "LOST":
                if dist <= threshold:
                    # вернулся — снова подтверждаем
                    state = "FOUND"
                    state_start = now
                    on_status("FOUND", state_start)
                elif elapsed >= START_TIMEOUT:
                    state = "WAIT"
                    state_start = now
                    on_status("WAIT", None)

            elif state == "FIX":
                # снимаем синхронно в FOUND; сюда не приходим пока идёт захват
                pass

            elif state == "ANALYZING":
                pass  # ждём завершения analyze_photos (блокирующий вызов)

            elif state == "DONE":
                if dist > threshold:
                    state = "COOLDOWN"
                    state_start = now
                    on_status("COOLDOWN", state_start)

            elif state == "COOLDOWN":
                if dist <= threshold:
                    # объект вернулся слишком быстро
                    state = "TOO_FAST"
                    state_start = now
                    on_status("TOO_FAST", None)
                elif elapsed >= cooldown:
                    state = "WAIT"
                    state_start = now
                    on_status("WAIT", None)

            elif state == "TOO_FAST":
                if dist > threshold:
                    # отодвинули — снова ждём готовность
                    state = "COOLDOWN"
                    state_start = now
                    on_status("COOLDOWN", state_start)

            time.sleep(0.05)

    finally:
        close_distance()