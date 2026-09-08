"""Общие блоки-виджеты для экранов.

Каждый блок отдельный виджет: DistanceBlock, StatusBlock, CamerasBlock,
ResultBlock. Экраны делают yield нужных виджетов.

CamerasBlock умеет снимать сам: при монтировании запускает съёмку и
обновляет свою таблицу. Параметр auto_capture=False отключает это.
"""

import time

from rich import box
from rich.table import Table
from rich.text import Text
from textual.containers import Vertical
from textual.widgets import Digits, LoadingIndicator, Static

from camera_capture import CAMERAS
from screens import workers
from settings import Settings


class DistanceBlock(Static):
    def __init__(self, auto_loop=True):
        self.auto_loop = auto_loop
        self.stopped = True
        super().__init__()
        self.border_title = "Дистанция"
        self.styles.border = ("solid", "cyan")
        self.styles.border_title_align = "center"
        self.styles.padding = (1, 2)
        self.styles.width = 30
        self.styles.align = ("center", "middle")

    def compose(self):
        yield Digits("—")

    def on_mount(self):
        # Digits — виджет со своим контентом: без text-align:center цифры
        # прижимаются влево, а text-style:bold включает насыщенный вариант
        # шрифта (DIGITS3X3_BOLD) — цифры выглядят жирнее/заметнее.
        digits = self.query_one(Digits)
        digits.styles.text_align = "center"
        digits.styles.text_style = "bold"
        if self.auto_loop:
            self.stopped = False
            self.run_worker(self._loop, thread=True)

    def on_unmount(self):
        self.stopped = True

    def _loop(self):
        workers.distance_loop(self._update, lambda: self.stopped)

    def _update(self, dist):
        """Вызывается из фонового потока дальномера — маришалим на главный."""
        self.app.call_from_thread(self._set_value, self._fmt(dist))

    def set_distance(self, dist):
        """Вызывается с главного потока (инспекция через call_from_thread)."""
        self._set_value(self._fmt(dist))

    @staticmethod
    def _fmt(dist):
        return "нет данных" if dist is None else str(dist)

    def _set_value(self, text):
        """Только на главном потоке."""
        try:
            self.query_one(Digits).update(text)
        except Exception:
            # экран уже закрыт — нечего обновлять
            pass


class StatusBlock(Static):
    """Текущее состояние инспекции (без рамки).

    set_state(key, started_at): key — одно из WAIT/FOUND/FIX/ANALYZING/
    DONE/COOLDOWN/TOO_FAST/LOST. started_at — время начала состояния
    (monotonic), для состояний с обратным отсчётом/живым таймером.
    """

    _LABELS = {
        "WAIT": "Ожидаем объект",
        "FOUND": "Объект найден",
        "FIX": "Фиксируем",
        "ANALYZING": "Анализируем",
        "DONE": "Готово",
        "COOLDOWN": "Ждем готовность",
        "TOO_FAST": "Слишком быстро, отодвиньте объект",
        "LOST": "Объект пропал",
    }
    _STYLES = {
        "WAIT": "grey",
        "FOUND": "yellow",
        "FIX": "yellow",
        "ANALYZING": "yellow",
        "DONE": "green",
        "COOLDOWN": "yellow",
        "TOO_FAST": "red",
        "LOST": "red",
    }

    _state = None
    _started = None

    def on_mount(self):
        self.set_interval(0.1, self._tick)

    def set_state(self, key, started_at):
        self._state = key
        self._started = started_at
        self._tick()

    def _tick(self):
        text = self._render_text()
        style = self._STYLES.get(self._state, "grey")
        self.update(Text(text, style=style))

    def _render_text(self):
        key = self._state
        if key is None:
            return "—"
        label = self._LABELS.get(key, key)
        elapsed = 0.0
        if self._started is not None:
            elapsed = time.time() - self._started

        if key == "FOUND":
            remaining = max(0.0, Settings.detect_time - elapsed)
            return f"{label} {remaining:.1f}с"
        if key == "ANALYZING":
            return f"{label} {elapsed:.1f}с"
        if key == "COOLDOWN":
            remaining = max(0.0, Settings.cooldown - elapsed)
            return f"{label} {remaining:.1f}с"
        return label


class ResultBlock(Vertical):
    """Блок "Анализ": спиннер при анализе, иначе тело результата/ошибка.

    Два дочерних виджета: LoadingIndicator (спиннер) и Static(id="body").
    Переключаем их display — каждый рендерится своим механизмом, без
    смешивания composed-детей и update() на контейнере.
    """

    _front = "—"
    _side = "—"
    _conf = "—"
    _reason = "—"
    _error = None
    _analyzing = False

    def __init__(self):
        super().__init__()
        self.border_title = "Анализ"
        self.styles.border = ("solid", "cyan")
        self.styles.border_title_align = "center"
        self.styles.padding = (1, 2)

    def compose(self):
        yield LoadingIndicator(id="analysis-loading")
        yield Static(id="analysis-body")

    def on_mount(self):
        self.query_one("#analysis-loading").styles.height = "100%"
        self._show_body()

    def set_analyzing(self, on):
        self._analyzing = on
        if on:
            self._error = None  # свежий цикл — не тащим прошлую ошибку в спиннер
        self._show_body()

    def set_result(self, result):
        self._analyzing = False
        self._error = None
        self._front = result.get("angle_front_deg", "—")
        self._side = result.get("angle_side_deg", "—")
        self._conf = result.get("confidence", "—")
        self._reason = result.get("reason", "—")
        self._show_body()

    def set_error(self, message):
        self._analyzing = False
        self._error = message
        self._show_body()

    def _body(self):
        return (f"Спереди: {self._front}°\n"
                f"Сбоку: {self._side}°\n"
                f"Уверенность: {self._conf}\n"
                f"Комментарий: {self._reason}")

    def _show_body(self):
        loading = self.query_one("#analysis-loading")
        body = self.query_one("#analysis-body")
        loading.display = self._analyzing
        body.display = not self._analyzing
        if not self._analyzing:
            if self._error is not None:
                body.update(Text(self._error, style="bold red"))
            else:
                body.update(self._body())


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
        self._durations = {}  # cam -> секунды съёмки (в колонку Time)
        self._last_times = {}  # cam -> длительность прошлого запуска (в колонку Last time)
        self._statuses = {}   # cam -> (status, detail)
        super().__init__()
        self.border_title = "Камеры"
        self.styles.border = ("solid", "cyan")
        self.styles.border_title_align = "left"
        self.styles.padding = (1, 1)

    def on_mount(self):
        for cam_idx in CAMERAS:
            self._statuses[cam_idx] = ("OK", "")
        self._redraw()
        self.set_interval(0.1, self._tick)
        if self.auto_capture:
            self.run_worker(self._capture, thread=True)

    def _tick(self):
        if self._starts:
            self._redraw()

    def _redraw(self):
        table = Table(expand=True, box=box.SIMPLE, show_edge=False, pad_edge=False)
        table.add_column("#", justify="left", ratio=1)
        table.add_column("Status", ratio=8)
        table.add_column("Last time", justify="right", ratio=2)
        table.add_column("Time", justify="right", ratio=2)

        for cam_idx in CAMERAS:
            status, detail = self._statuses.get(cam_idx, ("OK", ""))
            text = status if not detail else f"{status}: {detail}"
            style = self.STATUS_STYLE.get(status, "bold green")

            last = "—"
            if cam_idx in self._last_times:
                last = f"{self._last_times[cam_idx]:.1f} c"

            time_val = "—"
            start = self._starts.get(cam_idx)
            if start is not None:
                time_val = f"{time.monotonic() - start:.1f} c"
            elif cam_idx in self._durations:
                time_val = f"{self._durations[cam_idx]:.1f} c"

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
        self._last_times = {cam: dur for cam, dur in self._durations.items()}
        self._durations = {}
        self._starts = {}
        self._statuses = {cam: ("OK", "") for cam in CAMERAS}
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
            # переносим завершённый таймер в "Last time" (для инспекции, где
            # restart() не используется, колонка иначе вечно была бы "—")
            if cam_idx not in self._last_times:
                self._last_times[cam_idx] = duration
            self._statuses[cam_idx] = (status, detail)
        self._redraw()