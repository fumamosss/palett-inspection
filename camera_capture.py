"""
Захват фото с двух USB-камер на Windows.

ПРОБЕЛ - сделать снимки со всех камер, Q - выход.
Камеры открываются только в момент съёмки (не висят в фоне, не греют USB-шину).
"""

import msvcrt
import os
import time
from datetime import datetime

import cv2

CAPTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captures")
CAMERAS = [0, 1]        # индексы двух камер
CAPTURE_DELAY = 1.0     # пауза между камерами (USB-шина не держит две сразу), сек
READ_RETRIES = 5        # попыток прочитать кадр
WIDTH, HEIGHT = 1280, 960   # разрешение захвата


def find_cameras() -> list[int]:
    """Возвращает индексы открываемых камер."""
    return [i for i in CAMERAS if open_camera(i) is not None]


def fourcc_to_str(fourcc: int) -> str:
    """Корректно расшифровывает FOURCC (младший байт первый)."""
    return "".join(chr((fourcc >> (8 * k)) & 0xFF) for k in range(4))


def open_camera(index: int) -> cv2.VideoCapture | None:
    """Открывает камеру, ставит разрешение (без форсирования кодека)."""
    t = time.monotonic()
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    t_created = time.monotonic() - t
    if not cap.isOpened():
        print(f"[DBG cam{index}] VideoCapture не открылся за {t_created:.2f}с")
        cap.release()
        return None
    # Ставим желаемое разрешение (без принудительного MJPG - он ломает формат)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    # Фактические параметры после set
    codec = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec_s = fourcc_to_str(codec)
    w_actual = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_actual = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"[DBG cam{index}] open {t_created:.2f}с | формат {codec_s} | "
          f"разрешение {w_actual}x{h_actual} | fps ~{fps:.0f}")
    return cap


def read_frame(cap: cv2.VideoCapture):
    """Читает первый валидный кадр с несколькими попытками."""
    t = time.monotonic()
    for _ in range(READ_RETRIES):
        ok, frame = cap.read()
        if ok and frame is not None and frame.size > 0:
            return frame, True, time.monotonic() - t
        time.sleep(0.3)
    return None, False, time.monotonic() - t


def capture_once(cameras: list[int], out_dir: str) -> None:
    """Снимает последовательно: открыть -> кадр -> закрыть, с паузой между камерами.

    Дешёвые USB-камеры на одной шине не могут быть открыты одновременно,
    поэтому открываем и снимаем по одной, с паузой между ними.
    """
    os.makedirs(out_dir, exist_ok=True)
    t_total = time.monotonic()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, index in enumerate(cameras):
        if i > 0:
            time.sleep(CAPTURE_DELAY)  # даём шине освободиться

        t0 = time.monotonic()
        cap = open_camera(index)
        if cap is None:
            print(f"[ERR] камера {index} не открылась")
            continue

        frame, ok_read, read_s = read_frame(cap)
        cap.release()  # снова «спит»

        if not ok_read:
            print(f"[ERR] камера {index}: кадр не получен ({read_s:.2f}с)")
            continue

        path = os.path.join(out_dir, f"cam{index}_{ts}.jpg")
        if cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95]):
            h, w = frame.shape[:2]
            print(f"[OK] {os.path.basename(path)} | {w}x{h} | "
                  f"кадр {read_s:.2f}с | всего {time.monotonic() - t0:.2f}с")
        else:
            print(f"[ERR] камера {index}: не удалось сохранить")

    print(f"-- съёмка заняла {time.monotonic() - t_total:.1f}с")


def main() -> None:
    cameras = find_cameras()
    if not cameras:
        print("Камеры не найдены.")
        return

    print(f"Камеры: {cameras}")
    print("ПРОБЕЛ - снимок, Q - выход")

    while True:
        # msvcrt.getch() ждёт клавишу в консоли (работает в cmd/PowerShell)
        key = msvcrt.getch().lower()
        if key in (b"q", b"\x1b"):   # Q или Esc
            break
        if key == b" ":              # ПРОБЕЛ
            capture_once(cameras, CAPTURE_DIR)

    print("Выход.")


if __name__ == "__main__":
    main()
