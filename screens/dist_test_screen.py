"""Экран теста дальномера."""

from textual.screen import Screen
from textual.widgets import Footer

from service_panel import DistanceBlock


class DistTestScreen(Screen):
    BINDINGS = [("escape", "back", "Назад")]

    def compose(self):
        yield DistanceBlock()
        yield Footer()

    def action_back(self):
        self.app.pop_screen()