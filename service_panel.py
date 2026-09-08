"""Общие блоки-виджеты для экранов.

Каждый блок отдельный виджет: DistanceBlock, StateBlock, CamerasBlock.
Экраны делают yield нужных виджетов.

CamerasBlock умеет снимать сам: при монтировании запускает съёмку и
обновляет свою таблицу. Параметр auto_capture=False отключает это.
"""

import time

from rich.text import Text
from textual.widgets import DataTable, Digits, Static

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
        super().__init__()
        self.border_title = "Камеры"
        self.styles.border = ("round", "cyan")
        self.styles.border_title_align = "center"
        self.styles.padding = (1, 1)

    def compose(self):
        yield DataTable()

    def on_mount(self):
        table = self.query_one(DataTable)
        table.cursor_type = "none"
        self.col_num = table.add_column("#", width=4)
        self.col_status = table.add_column("Status", width=60)
        self.col_last = table.add_column("Last time", width=14)
        self.col_time = table.add_column("Time", width=14)
        self.rows = {}
        for cam_idx in CAMERAS:
            self.rows[cam_idx] = table.add_row(
                str(cam_idx),
                Text("OK", style=self.STATUS_STYLE["OK"]),
                "—", "—",
            )
        if self.auto_capture:
            self.run_worker(self._capture, thread=True)

    def _capture(self):
        workers.cameras_capture(self._on_status)

    def restart(self):
        """Перезапустить съёмку: прошлые Time уходят в Last time."""
        table = self.query_one(DataTable)
        for cam_idx in CAMERAS:
            duration = self._durations.pop(cam_idx, None)
            table.update_cell(self.rows[cam_idx], self.col_last,
                              f"{duration:.1f} c" if duration is not None else "—")
            table.update_cell(self.rows[cam_idx], self.col_time, "—")
            table.update_cell(self.rows[cam_idx], self.col_status,
                              Text("OK", style=self.STATUS_STYLE["OK"]))
        self.run_worker(self._capture, thread=True)

    def _on_status(self, cam_idx, status, detail):
        try:
            self.app.call_from_thread(self._apply_status, cam_idx, status, detail)
        except Exception:
            pass

    def _apply_status(self, cam_idx, status, detail):
        table = self.query_one(DataTable)
        if status == "TAKING":
            self._starts[cam_idx] = time.monotonic()
            text = "TAKING"
        else:
            start = self._starts.pop(cam_idx, None)
            duration = (time.monotonic() - start) if start is not None else 0.0
            self._durations[cam_idx] = duration
            table.update_cell(self.rows[cam_idx], self.col_time, f"{duration:.1f} c")
            text = status if not detail else f"{status}: {detail}"
        table.update_cell(self.rows[cam_idx], self.col_status,
                          Text(text, style=self.STATUS_STYLE[status]))


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