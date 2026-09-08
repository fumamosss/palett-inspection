"""Экран теста камер."""

from textual.screen import Screen
from textual.widgets import Footer

from service_panel import PhotosBlock


class CamTestScreen(Screen):
    BINDINGS = [("escape", "back", "Назад")]

    def compose(self):
        yield PhotosBlock()
        yield Footer()

    def action_back(self):
        self.app.pop_screen()