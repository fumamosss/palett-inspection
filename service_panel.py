"""Общие блоки-виджеты для экранов.

Каждый блок отдельный виджет: DistanceBlock, StateBlock, PhotosBlock.
Экраны делают yield нужных виджетов.

PhotosBlock умеет снимать сам: при монтировании запускает съёмку и
обновляет свой текст. Параметр auto_capture=False отключает это
(например, внутри ServicePanel, где съёмкой управляет инспекция).
"""

from textual.widgets import Digits, Static

from camera_capture import capture_photos
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


class PhotosBlock(Static):
    def __init__(self, auto_capture=True):
        self.auto_capture = auto_capture
        super().__init__("Фото: —")

    def on_mount(self):
        if self.auto_capture:
            self.run_worker(self._capture, thread=True)

    def _capture(self):
        self._set_text("Фото: съёмка...")
        photos = capture_photos()
        self._set_photos(photos)

    def _set_text(self, text):
        try:
            self.app.call_from_thread(self.update, text)
        except Exception:
            # exe уже закрыт экран — нечего обновлять
            pass

    def set_photos(self, paths):
        self._set_photos(paths)

    def _set_photos(self, paths):
        if not paths:
            self._set_text("Фото: не сохранены")
        else:
            joined = ", ".join(p.rsplit("\\", 1)[-1] for p in paths)
            self._set_text(f"Фото: {joined}")

    def set_photo_error(self, message):
        self._set_text(f"Фото: {message}")


class ServicePanel(Static):
    def compose(self):
        yield DistanceBlock(auto_loop=False)
        yield StateBlock()
        yield PhotosBlock(auto_capture=False)

    def set_distance(self, dist):
        self.query_one(DistanceBlock).set_distance(dist)

    def set_state(self, state):
        self.query_one(StateBlock).set_state(state)

    def set_photos(self, paths):
        self.query_one(PhotosBlock).set_photos(paths)

    def set_photo_error(self, message):
        self.query_one(PhotosBlock).set_photo_error(message)