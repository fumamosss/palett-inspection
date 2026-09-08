"""TUI-меню приложения (textual).

Пункты меню запускают операции через app.exit(код_действия):
  - "inspect"    -> запустить цикл инспекции
  - "dist_test"  -> тест дальномера
  - "cam_test"   -> тест камер
  - None         -> просто выход (q)

Значения настроек живут в settings.Settings и сохраняются в settings.json.
"""

from textual.app import App
from textual.screen import Screen
from textual.widgets import OptionList, Footer, Input, Label
from textual.widgets.option_list import Option

from settings import Settings

# Описания пунктов экрана настроек (показываются под списком при наведении)
SETTING_DESCRIPTIONS = {
    "threshold": "Расстояние в см, ближе которого датчик считает, что объект появился на стенде.",
    "detect": "Сколько секунд объект должен непрерывно стоять на стенде, чтобы запустился анализ.",
    "cooldown": "Сколько секунд стенд должен пустовать, чтобы система была готова к следующему объекту.",
    "reset": "Вернуть все настройки к значениям по умолчанию.",
}


# ------------------- Экран настроек -------------------
class SettingsScreen(Screen):
    BINDINGS = [("escape", "back", "Назад")]

    def compose(self):
        yield OptionList(
            Option(f"Порог расстояния: {Settings.threshold} см", id="threshold"),
            Option(f"Время детекта: {Settings.detect_time} сек", id="detect"),
            Option(f"Кулдаун: {Settings.cooldown} сек", id="cooldown"),
            Option("Сбросить настройки", id="reset"),
        )
        yield Label("", id="setting_desc")
        yield Input(placeholder="значение", id="value_input")
        yield Footer()

    def on_mount(self):
        self.query_one("#value_input").display = False

    def on_option_list_option_highlighted(self, event):
        label = self.query_one("#setting_desc")
        label.update(SETTING_DESCRIPTIONS.get(event.option_id, ""))

    def on_option_list_option_selected(self, event):
        option_id = event.option_id

        if option_id == "reset":
            Settings.reset()
            self.notify("Настройки сброшены к значениям по умолчанию")
            self.update_options()
            return

        self.editing = option_id
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
            self.query_one("#value_input").value = ""
            return
        if value <= 0:
            self.query_one("#value_input").value = ""
            return

        if self.editing == "threshold":
            Settings.threshold = int(value)
        elif self.editing == "detect":
            Settings.detect_time = value
        elif self.editing == "cooldown":
            Settings.cooldown = value
        Settings.save()

        inp = self.query_one("#value_input")
        inp.value = ""
        inp.display = False
        self.update_options()
        self.query_one(OptionList).focus()

    def update_options(self):
        ol = self.query_one(OptionList)
        ol.clear_options()
        ol.add_option(Option(f"Порог расстояния: {Settings.threshold} см", id="threshold"))
        ol.add_option(Option(f"Время детекта: {Settings.detect_time} сек", id="detect"))
        ol.add_option(Option(f"Кулдаун: {Settings.cooldown} сек", id="cooldown"))
        ol.add_option(Option("Сбросить настройки", id="reset"))

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
            self.app.exit("inspect")
        elif option_id == "dist_test":
            self.app.exit("dist_test")
        elif option_id == "cam_test":
            self.app.exit("cam_test")
        elif option_id == "settings":
            self.app.push_screen(SettingsScreen())
        elif option_id == "exit":
            self.app.exit()


class MenuApp(App):
    TITLE = "Pallet Inspection"
    BINDINGS = [("q", "quit", "Выход")]

    def on_mount(self):
        Settings.load()
        self.push_screen(MainMenu())


if __name__ == "__main__":
    MenuApp().run()