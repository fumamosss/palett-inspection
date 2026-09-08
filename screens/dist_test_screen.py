"""Экран теста дальномера."""

from textual.screen import Screen
from textual.widgets import Footer

from service_panel import DistanceBlock
from screens import workers


class DistTestScreen(Screen):
    BINDINGS = [("escape", "back", "Назад")]

    def compose(self):
        yield DistanceBlock()
        yield Footer()

    def on_mount(self):
        self.stopped = False
        block = self.query_one(DistanceBlock)

        def on_update(dist, state, photos):
            if dist is not None:
                block.set_distance(dist)

        self.run_worker(
            lambda: workers.distance_loop(on_update, lambda: self.stopped),
            thread=True,
        )

    def on_unmount(self):
        self.stopped = True

    def action_back(self):
        self.app.pop_screen()