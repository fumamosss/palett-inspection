"""Экран теста камер."""

from textual.screen import Screen
from textual.widgets import Footer

from service_panel import PhotosBlock
from screens import workers


class CamTestScreen(Screen):
    BINDINGS = [("escape", "back", "Назад")]

    def compose(self):
        yield PhotosBlock()
        yield Footer()

    def on_mount(self):
        self.stopped = False
        block = self.query_one(PhotosBlock)

        def on_update(dist, state, photos):
            if photos is not None:
                block.set_photos(photos)

        self.run_worker(
            lambda: workers.camera_test(on_update, lambda: self.stopped),
            thread=True,
        )

    def on_unmount(self):
        self.stopped = True

    def action_back(self):
        self.app.pop_screen()