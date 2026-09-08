"""Экран теста камер."""

from textual.screen import Screen
from textual.widgets import Footer

from service_panel import CamerasBlock


class CamTestScreen(Screen):
    BINDINGS = [
        ("escape", "back", "Назад"),
        ("r", "recapture", "Снять заново"),
    ]

    def compose(self):
        yield CamerasBlock()
        yield Footer()

    def action_recapture(self):
        self.query_one(CamerasBlock).restart()

    def action_back(self):
        self.app.pop_screen()