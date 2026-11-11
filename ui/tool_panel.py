from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QToolButton,
    QButtonGroup,
)


class ToolPanel(QFrame):
    """Вертикальная панель инструментов САПР."""

    # Сигнал передаёт название выбранного инструмента.
    tool_changed = Signal(str)

    def __init__(self, controller):
        super().__init__()

        # Сохраняем ссылку на контроллер приложения.
        self.controller = controller

        # Настраиваем внешний вид панели.
        self.setFixedWidth(80)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # Создаём вертикальное расположение элементов.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Группа обеспечивает выбор только одной кнопки.
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # Сохраняем кнопки по названиям инструментов.
        self.buttons = {}

        # Создаём только необходимые инструменты.
        self.create_tool_button(
            layout, "segment", "Отрезок"
        )
        self.create_tool_button(
            layout, "delete", "Удалить"
        )

        # Оставшееся место занимает пустое пространство.
        layout.addStretch()

    def create_tool_button(self, layout, tool_name, title):
        """Создаёт кнопку и подключает её к контроллеру."""

        button = QToolButton()
        button.setText(title)

        # Кнопку можно оставить нажатой.
        button.setCheckable(True)

        # Располагаем текст кнопки под значком.
        button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )

        # Добавляем кнопку в группу.
        self.button_group.addButton(button)
        self.buttons[tool_name] = button

        # Сохраняем оформление кнопок.
        button.setStyleSheet("""
            QToolButton {
                padding: 8px 2px;
                border: 1px solid transparent;
                border-radius: 5px;
            }

            QToolButton:checked {
                background-color: #D6E8FF;
                border: 1px solid #4A90E2;
            }

            QToolButton:hover {
                border: 1px solid #9BBCE5;
            }
        """)

        # При нажатии передаём выбор контроллеру.
        button.clicked.connect(
            lambda checked=False, name=tool_name:
                self.select_tool(name)
        )

        layout.addWidget(button)

    def select_tool(self, tool_name):
        """Выбирает инструмент через контроллер."""

        accepted = self.controller.set_tool(tool_name)

        if accepted:
            self.set_current_tool(tool_name)

            # Сообщаем рабочей области о смене инструмента.
            self.tool_changed.emit(tool_name)
        else:
            # Возвращаем выделение к текущему инструменту.
            self.set_current_tool(
                self.controller.current_tool
            )

    def set_current_tool(self, tool_name):
        """Устанавливает подсветку выбранного инструмента."""

        button = self.buttons.get(tool_name)

        if button is not None:
            button.setChecked(True)
        else:
            # Если инструмент сброшен, снимаем выделение.
            self.button_group.setExclusive(False)

            for tool_button in self.buttons.values():
                tool_button.setChecked(False)

            self.button_group.setExclusive(True)
