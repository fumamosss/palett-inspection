from textual.app import App, ComposeResult
from textual.widgets import OptionList, Footer
from textual.widgets.option_list import Option


class MenuApp(App):
    TITLE = "Pallet Inspection"
    BINDINGS = [("q", "quit", "Выход")]

    def compose(self) -> ComposeResult:
        yield OptionList(
            Option("Запустить", id="run"),
            Option("Тест дальномера", id="dist_test"),
            Option("Тест камер", id="cam_test"),
            Option("Настройки", id="settings"),
            Option("Выход", id="exit"),
        )
        yield Footer()

    def on_option_list_option_selected(self, event):
        option_id = event.option_id

        if option_id == "run":
            self.notify("Запустить (ещё не подключено)")
        elif option_id == "settings":
            self.notify("Настройки (ещё не подключены)")
        elif option_id == "dist_test":
            self.notify("Тест дальномера (ещё не подключен)")
        elif option_id == "cam_test":
            self.notify("Тест камер (ещё не подключен)")
        elif option_id == "exit":
            self.exit()


if __name__ == "__main__":
    MenuApp().run()