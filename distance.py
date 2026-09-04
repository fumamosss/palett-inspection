"""Модуль дальномера VL53L1X через CH341T (Windows).

Функции:
  open_distance() -> bool
    Открыть CH341 и инициализировать VL53L1X.
  get_distance() -> int | None
    Прочитать расстояние в мм (None = нет данных).
  close_distance()
    Закрыть CH341.
"""

import ctypes
import time

DLL = r"C:\Windows\System32\CH341DLLA64.DLL"
I2C_W = 0x29 << 1  # 0x52

dll = ctypes.WinDLL(DLL)
dll.CH341OpenDevice.argtypes = [ctypes.c_ulong]
dll.CH341OpenDevice.restype = ctypes.c_void_p
dll.CH341CloseDevice.argtypes = [ctypes.c_ulong]
dll.CH341CloseDevice.restype = None
dll.CH341SetStream.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
dll.CH341SetStream.restype = ctypes.c_bool
dll.CH341StreamI2C.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                               ctypes.c_ulong, ctypes.c_void_p]
dll.CH341StreamI2C.restype = ctypes.c_bool

# ST default config 0x2D..0x87 (из Adafruit VL53L1X)
_INIT_SEQ = bytes([
    0x00, 0x00, 0x00, 0x01, 0x02, 0x00, 0x02, 0x08, 0x00, 0x08, 0x10, 0x01,
    0x01, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x20, 0x0B, 0x00, 0x00, 0x02, 0x0A, 0x21, 0x00, 0x00, 0x05, 0x00,
    0x00, 0x00, 0x00, 0xC8, 0x00, 0x00, 0x38, 0xFF, 0x01, 0x00, 0x08, 0x00,
    0x00, 0x01, 0xCC, 0x0F, 0x01, 0xF1, 0x0D, 0x01, 0x68, 0x00, 0x80, 0x08,
    0xB8, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x89, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x0F, 0x0D, 0x0E, 0x0E, 0x00, 0x00, 0x02, 0xC7, 0xFF,
    0x9B, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
])

_initialized = False


def _stream(write, nread):
    wb = (ctypes.c_ubyte * len(write))(*write)
    rb = (ctypes.c_ubyte * nread)() if nread else None
    ok = dll.CH341StreamI2C(0, len(write), wb, nread,
                            rb if rb is not None else ctypes.cast(None, ctypes.c_void_p))
    return bool(ok), (bytes(rb) if rb is not None else b"")


def _read8(reg):
    ok, d = _stream([I2C_W, (reg >> 8) & 0xFF, reg & 0xFF], 1)
    return d[0] if ok else None


def _read2(reg):
    ok, d = _stream([I2C_W, (reg >> 8) & 0xFF, reg & 0xFF], 2)
    return (d[0] << 8) | d[1] if ok and len(d) >= 2 else None


def _write8(reg, val):
    return _stream([I2C_W, (reg >> 8) & 0xFF, reg & 0xFF, val & 0xFF], 0)[0]


def _write_block(reg, data):
    return _stream([I2C_W, (reg >> 8) & 0xFF, reg & 0xFF] + list(data), 0)[0]


def open_distance() -> bool:
    """Открыть CH341 и инициализировать VL53L1X. Возвращает True если ОК."""
    global _initialized
    h = dll.CH341OpenDevice(0)
    if h in (None, 0, -1, 0xFFFFFFFFFFFFFFFF):
        return False
    dll.CH341SetStream(0, 1)

    if _read8(0x010F) != 0xEA:
        dll.CH341CloseDevice(0)
        return False

    _write_block(0x002D, _INIT_SEQ)
    # ROI 4x4 SPAD (вместо 16x16 по умолчанию) — узкий конус
    _write8(0x007F, 0x77)   # центр ROI (середина 16x16 массива)
    _write8(0x0080, 0x33)   # размер ROI: X=3, Y=3 → 4x4
    _write8(0x0087, 0x40)
    t = 0
    while _read8(0x0089) != 0x09 and t < 200:
        time.sleep(0.01)
        t += 1
    _write8(0x0086, 0x01)
    _write8(0x0087, 0x00)
    _write8(0x0008, 0x09)
    _write8(0x000B, 0x00)
    _initialized = True
    return True


def get_distance() -> int | None:
    """Прочитать расстояние. None = нет данных / нет цели."""
    if not _initialized:
        return None
    _write8(0x0087, 0x40)  # старт
    t = 0
    while _read8(0x0089) != 0x09 and t < 200:
        time.sleep(0.01)
        t += 1
    # Читаем ТОЛЬКО если статус = 0x09 (успех)
    if _read8(0x0089) == 0x09:
        dist = _read2(0x0096)
        _write8(0x0086, 0x01)
        return dist // 10 if dist is not None else None
    else:
        _write8(0x0086, 0x01)
        return None


def close_distance():
    """Закрыть CH341."""
    global _initialized
    if _initialized:
        _write8(0x0087, 0x00)
        dll.CH341CloseDevice(0)
        _initialized = False


# для ручного запуска: python distance.py
if __name__ == "__main__":
    if open_distance():
        print("Дальномер готов. Ctrl+C для выхода.")
        try:
            while True:
                print(get_distance())
                time.sleep(0.05)
        except KeyboardInterrupt:
            pass
        finally:
            close_distance()
    else:
        print("Дальномер не найден.")
