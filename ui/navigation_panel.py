
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QToolButton,
)


class NavigationPanel(QWidget):
    """Панель навигации рабочей области."""

    hand_clicked = Signal()
    zoom_in_clicked = Signal()
    zoom_out_clicked = Signal()
    fit_all_clicked = Signal()
    rotate_left_clicked = Signal()
    rotate_right_clicked = Signal()
    reset_view_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 4, 5, 4)
        layout.setSpacing(6)

        # Инструмент перемещения.
        self.hand_button = self.create_button("Рука", "Перемещение рабочей области")
        self.hand_button.setCheckable(True)
        self.hand_button.clicked.connect(self.hand_clicked.emit)
        layout.addWidget(self.hand_button)

        # Увеличение масштаба.
        zoom_in_button = self.create_button("Zoom +", "Увеличить масштаб")
        zoom_in_button.clicked.connect(self.zoom_in_clicked.emit)
        layout.addWidget(zoom_in_button)

        # Уменьшение масштаба.
        zoom_out_button = self.create_button("Zoom −", "Уменьшить масштаб")
        zoom_out_button.clicked.connect(self.zoom_out_clicked.emit)
        layout.addWidget(zoom_out_button)

        # Показать весь чертёж.
        fit_all_button = self.create_button("Показать всё", "Вписать весь чертёж")
        fit_all_button.clicked.connect(self.fit_all_clicked.emit)
        layout.addWidget(fit_all_button)

        layout.addSpacing(12)

        # Поворот рабочей области.
        rotate_left_button = self.create_button("↶", "Поворот налево")
        rotate_left_button.clicked.connect(self.rotate_left_clicked.emit)
        layout.addWidget(rotate_left_button)

        rotate_right_button = self.create_button("↷", "Поворот направо")
        rotate_right_button.clicked.connect(self.rotate_right_clicked.emit)
        layout.addWidget(rotate_right_button)

        layout.addSpacing(12)

        # Сброс вида.
        reset_button = self.create_button("Сбросить вид", "Вернуть исходный вид")
        reset_button.clicked.connect(self.reset_view_clicked.emit)
        layout.addWidget(reset_button)

        layout.addStretch()

    def create_button(self, text, tooltip):
        """Создаёт кнопку панели навигации."""

        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.setAutoRaise(False)

        return button

    def set_hand_active(self, active):
        """Обновляет состояние кнопки Рука."""

        self.hand_button.setChecked(active)
