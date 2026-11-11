
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    # Создаём приложение
    app = QApplication(sys.argv)

    # Определяем путь к файлу стилей
    style_path = Path(__file__).parent / "styles" / "style.qss"

    # Загружаем и применяем стили
    with open(style_path, "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())

    # Создаём главное окно
    window = MainWindow()
    window.show()

    # Запускаем цикл обработки событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
