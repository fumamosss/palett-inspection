"""Общие блоки-виджеты для экранов.

ServicePanel — панель с блоками дистанции/состояния/фото.
Каждый блок отдельный виджет: DistanceBlock, StateBlock, PhotosBlock.
Экраны просто делают yield ServicePanel() и обновляют через методы.
"""

from textual.widgets import Static


class DistanceBlock(Static):
    def __init__(self):
        super().__init__("Дистанция: —")

    def set_distance(self, dist):
        text = "нет данных" if dist is None else f"{dist} см"
        self.update(f"Дистанция: {text}")


class StateBlock(Static):
    def __init__(self):
        super().__init__("Состояние: —")

    def set_state(self, state):
        self.update(f"Состояние: {state}")


class PhotosBlock(Static):
    def __init__(self):
        super().__init__("Фото: —")

    def set_photos(self, paths):
        if not paths:
            self.update("Фото: не сохранены")
        else:
            joined = ", ".join(p.rsplit("\\", 1)[-1] for p in paths)
            self.update(f"Фото: {joined}")

    def set_photo_error(self, message):
        self.update(f"Фото: {message}")


class ServicePanel(Static):
    def compose(self):
        yield DistanceBlock()
        yield StateBlock()
        yield PhotosBlock()

    def set_distance(self, dist):
        self.query_one(DistanceBlock).set_distance(dist)

    def set_state(self, state):
        self.query_one(StateBlock).set_state(state)

    def set_photos(self, paths):
        self.query_one(PhotosBlock).set_photos(paths)

    def set_photo_error(self, message):
        self.query_one(PhotosBlock).set_photo_error(message)