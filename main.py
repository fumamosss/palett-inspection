"""Точка входа: запускает TUI-меню.

Запуск:  python main.py
Выход:   q в меню, Escape на экранах.
"""

from menu import MenuApp


def main():
    MenuApp().run()


if __name__ == "__main__":
    main()