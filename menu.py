from textual.app import App
from textual.screen import Screen
from textual.widgets import OptionList, Footer, Input
from textual.widgets.option_list import Option


# ------------------- настройки -------------------
class Settings:
    threshold = 50      # порог расстояния 
    detect_time = 1.5   # сколько времени должен находиться объект на стенде для запуска анализа
    cooldown = 2.0      # сколько времени стенд должен пустовать для готовности к следующему объекту


# ------------------- экран настроек -------------------
class SettingsScreen(Screen):
    BINDINGS = [("escape", "back", "Назад")]

    def compose(self):
        yield OptionList(
            Option(f"Порог расстояния: {Settings.threshold}", id="threshold"),
            Option(f"Время детекта: {Settings.detect_time} сек", id="detect"),
            Option(f"Кулдаун: {Settings.cooldown} сек", id="cooldown"),
        )
        yield Input(placeholder="значение", id="value_input")
        yield Footer()

    def on_mount(self):
        self.query_one("#value_input").display = False

    def on_option_list_option_selected(self, event):
        self.editing = event.option_id
        inp = self.query_one("#value_input")
        inp.placeholder = f"Новое значение (сейчас {self.current_value()})"
        inp.value = ""
        inp.display = True
        inp.focus()

    def current_value(self):
        return {
            "threshold": Settings.threshold,
            "detect": Settings.detect_time,
            "cooldown": Settings.cooldown,
        }[self.editing]

    def on_input_submitted(self, event):
        try:
            value = float(event.value)
        except ValueError:
            self.bell()
            self.query_one("#value_input").value = ""
            return
        if self.editing == "threshold":
            Settings.threshold = int(value)
        elif self.editing == "detect":
            Settings.detect_time = value
        elif self.editing == "cooldown":
            Settings.cooldown = value
        inp = self.query_one("#value_input")
        inp.value = ""
        inp.display = False
        self.update_options()
        self.query_one(OptionList).focus()

    def update_options(self):
        ol = self.query_one(OptionList)
        ol.clear_options()
        ol.add_option(Option(f"Порог расстояния: {Settings.threshold}", id="threshold"))
        ol.add_option(Option(f"Время детекта: {Settings.detect_time} сек", id="detect"))
        ol.add_option(Option(f"Кулдаун: {Settings.cooldown} сек", id="cooldown"))

    def action_back(self):
        self.app.pop_screen()


# ------------------- Главное меню -------------------
class MainMenu(Screen):
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
            # TODO: inspect_pallet() из main.py
            self.notify("Инспекция (ещё не подключена)")
        elif option_id == "dist_test":
            # TODO: тест дальномера
            self.notify("Тест дальномера (ещё не подключен)")
        elif option_id == "cam_test":
            # TODO: тест камер
            self.notify("Тест камер (ещё не подключен)")
        elif option_id == "settings":
            self.app.push_screen(SettingsScreen())
        elif option_id == "exit":
            self.app.exit()


class MenuApp(App):
    TITLE = "Pallet Inspection"
    BINDINGS = [("q", "quit", "Выход")]

    def on_mount(self):
        self.push_screen(MainMenu())


if __name__ == "__main__":
    MenuApp().run()