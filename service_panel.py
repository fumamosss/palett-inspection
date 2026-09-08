"""Общие блоки-виджеты для экранов.

Каждый блок отдельный виджет: DistanceBlock, StateBlock, CamerasBlock.
Экраны делают yield нужных виджетов.

CamerasBlock умеет снимать сам: при монтировании запускает съёмку и
обновляет свою таблицу. Параметр auto_capture=False отключает это.
"""

import time

from rich.table import Table
from rich.text import Text
from textual.widgets import Digits, Static

from camera_capture import CAMERAS, capture_photos
from screens import workers


class DistanceBlock(Static):
    def __init__(self, auto_loop=True):
        self.auto_loop = auto_loop
        self.stopped = True
        super().__init__()
        self.border_title = "Дистанция"
        self.styles.border = ("round", "blue")
        self.styles.border_title_align = "center"
        self.styles.padding = (1, 2)
        self.styles.width = 30

    def compose(self):
        yield Digits("—")

    def on_mount(self):
        if self.auto_loop:
            self.stopped = False
            self.run_worker(self._loop, thread=True)

    def on_unmount(self):
        self.stopped = True

    def _loop(self):
        workers.distance_loop(self._update, lambda: self.stopped)

    def _update(self, dist):
        self._set_value("нет данных" if dist is None else str(dist))

    def set_distance(self, dist):
        self._set_value("нет данных" if dist is None else str(dist))

    def _set_value(self, text):
        try:
            self.app.call_from_thread(self.query_one(Digits).update, text)
        except Exception:
            # экран уже закрыт — нечего обновлять
            pass


class StateBlock(Static):
    def __init__(self):
        super().__init__("Состояние: —")

    def set_state(self, state):
        self.update(f"Состояние: {state}")


class CamerasBlock(Static):
    STATUS_STYLE = {
        "OK": "bold green",
        "TAKING": "bold yellow",
        "SAVED": "bold green",
        "ERROR": "bold red",
    }

    def __init__(self, auto_capture=True):
        self.auto_capture = auto_capture
        self._starts = {}   # cam -> monotonic time начала съёмки
        self._durations = {}  # cam -> секунды последней съёмки
        self._statuses = {}   # cam -> (status, detail)
        super().__init__()
        self.border_title = "Камеры"
        self.styles.border = ("round", "cyan")
        self.styles.border_title_align = "center"
        self.styles.padding = (1, 1)

    def on_mount(self):
        for cam_idx in CAMERAS:
            self._statuses[cam_idx] = ("OK", "")
        self._redraw()
        if self.auto_capture:
            self.run_worker(self._capture, thread=True)

    def _redraw(self):
        table = Table(expand=True, show_edge=False, pad_edge=False)
        table.add_column("#", justify="left", ratio=1)
        table.add_column("Status", ratio=8)
        table.add_column("Last time", justify="right", ratio=2)
        table.add_column("Time", justify="right", ratio=2)

        for cam_idx in CAMERAS:
            status, detail = self._statuses.get(cam_idx, ("OK", ""))
            text = status if not detail else f"{status}: {detail}"
            style = self.STATUS_STYLE.get(status, "bold green")
            last = "—"
            if cam_idx in self._durations:
                last = f"{self._durations[cam_idx]:.1f} c"
            duration = self._starts.get(cam_idx)
            time_val = "—"
            if duration is not None:
                time_val = f"{time.monotonic() - duration:.1f} c"
            table.add_row(
                str(cam_idx),
                Text(text, style=style),
                last,
                time_val,
            )
        self.update(table)

    def _capture(self):
        workers.cameras_capture(self._on_status)

    def restart(self):
        """Перезапустить съёмку: прошлые Time уходят в Last time."""
        table_prev = self._durations
        self._durations = {}
        self._statuses = {cam: ("OK", "") for cam in CAMERAS}
        for cam_idx in CAMERAS:
            duration = table_prev.get(cam_idx)
            if duration is not None:
                self._durations[cam_idx] = duration
        self._redraw()
        self.run_worker(self._capture, thread=True)

    def _on_status(self, cam_idx, status, detail):
        try:
            self.app.call_from_thread(self._apply_status, cam_idx, status, detail)
        except Exception:
            pass

    def _apply_status(self, cam_idx, status, detail):
        if status == "TAKING":
            self._starts[cam_idx] = time.monotonic()
            self._statuses[cam_idx] = (status, detail)
        else:
            start = self._starts.pop(cam_idx, None)
            duration = (time.monotonic() - start) if start is not None else 0.0
            self._durations[cam_idx] = duration
            self._statuses[cam_idx] = (status, detail)
        self._redraw()


class ServicePanel(Static):
    def compose(self):
        yield DistanceBlock(auto_loop=False)
        yield StateBlock()
        yield CamerasBlock(auto_capture=False)

    def set_distance(self, dist):
        self.query_one(DistanceBlock).set_distance(dist)

    def set_state(self, state):
        self.query_one(StateBlock).set_state(state)

    def set_cam_status(self, cam_idx, status, detail=""):
        self.query_one(CamerasBlock)._apply_status(cam_idx, status, detail)