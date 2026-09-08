"""Главное меню (textual)."""

from textual.app import App
from textual.screen import Screen
from textual.widgets import OptionList, Footer
from textual.widgets.option_list import Option

from settings import Settings
from screens.settings_screen import SettingsScreen
from screens.dist_test_screen import DistTestScreen
from screens.cam_test_screen import CamTestScreen
from screens.inspection_screen import InspectionScreen


class MainMenu(Screen):
    BINDINGS = [("q", "quit", "Выход")]

    def compose(self):
        yield OptionList(
            Option("Запустить инспекцию", id="run"),
            Option("Тест дальномера", id="dist_test"),
            Option("Тест камер", id="cam_test"),
            Option("Настройки", id="settings"),
            Option("Выход", id="exit"),
        )
        yield Footer()

    def on_option_list_option_selected(self, event):
        option_id = event.option_id

        if option_id == "run":
            self.app.push_screen(InspectionScreen())
        elif option_id == "dist_test":
            self.app.push_screen(DistTestScreen())
        elif option_id == "cam_test":
            self.app.push_screen(CamTestScreen())
        elif option_id == "settings":
            self.app.push_screen(SettingsScreen())
        elif option_id == "exit":
            self.app.exit()


class MenuApp(App):
    TITLE = "Pallet Inspection"

    def on_mount(self):
        Settings.load()
        self.push_screen(MainMenu())


if __name__ == "__main__":
    MenuApp().run()