
import math

from PySide6.QtGui import QColor, QShortcut, QKeySequence, QGuiApplication
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QTabWidget,
    QToolButton,
    QMenu,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
    QSpinBox,
    QColorDialog,
    QGroupBox,
)

from app.controller import Controller
from ui.tool_panel import ToolPanel
from ui.drawarea import DrawingArea

from geometry.point import Point
from geometry.segment import Segment
from geometry.coordinates import polar_to_cartesian
from PySide6.QtCore import Qt, Signal
from ui.navigation_panel import NavigationPanel


class MainWindow(QMainWindow):
    """Главное окно приложения САПР."""

    def __init__(self):
        super().__init__()

        self.controller = Controller()

        # Последний отрезок, параметры которого отображаются.
        self.current_segment = None

        self.setWindowTitle("CAD — САПР")
        self.resize(1200, 800)

        # Основной контейнер окна.
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Верхняя панель.
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)


        # Основная область окна.
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # Левая колонка с информацией и настройками.
        self.side_panel = self.create_side_panel()
        self.side_panel.setFixedWidth(300)
        content_layout.addWidget(self.side_panel)

        # Панель инструментов редактирования.
        self.tool_panel = ToolPanel(self.controller)
        self.tool_panel.hide()
        content_layout.addWidget(self.tool_panel)

        # Правая область: навигация и чертёж.
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        # Панель навигации.
        self.navigation_panel = NavigationPanel()
        right_layout.addWidget(self.navigation_panel)

        # Рабочая область.
        self.drawing_area = DrawingArea()
        right_layout.addWidget(self.drawing_area, 1)
        
        # Обновление мировых координат курсора.
        self.drawing_area.cursor_position_changed.connect(
            self.update_cursor_info
        )

        # Обновление масштаба и угла поворота.
        self.drawing_area.view_changed.connect(
            self.update_view_info
        )

        # Подключение команд контекстного меню.
        self.drawing_area.hand_tool_requested.connect(
            self.activate_hand_tool
        )

        self.drawing_area.reset_view_requested.connect(
            self.reset_view
        )

        content_layout.addWidget(right_panel, 1)

        # Подключаем команды панели навигации.
        self.navigation_panel.hand_clicked.connect(
            self.activate_hand_tool
        )
        self.navigation_panel.zoom_in_clicked.connect(
            self.zoom_in
        )
        self.navigation_panel.zoom_out_clicked.connect(
            self.zoom_out
        )
        self.navigation_panel.fit_all_clicked.connect(
            self.drawing_area.fit_all
        )
        self.navigation_panel.rotate_left_clicked.connect(
            self.rotate_left
        )
        self.navigation_panel.rotate_right_clicked.connect(
            self.rotate_right
        )
        self.navigation_panel.reset_view_clicked.connect(
            self.reset_view
        )

        
        # Подключаем Fit All.
        self.fit_all_action.triggered.connect(self.drawing_area.fit_all)

        # Отображаем актуальные цвета на кнопках.
        self.update_color_buttons()
        
        # Создаём горячие клавиши для поворота рабочей области.
        self.create_shortcuts()

    # Связываем инструменты с рабочей областью.
        self.tool_panel.tool_changed.connect(
            self.activate_edit_tool
        )

        # Обновляем информацию при построении мышью.
        self.drawing_area.segment_created.connect(
            self.update_segment_info
        )

        # Обновляем информацию после удаления.
        self.drawing_area.segment_deleted.connect(
            self.update_info_after_deletion
        )

        # Синхронизируем начальный шаг сетки.
        self.change_grid_step(
            self.grid_step_input.value()
        )

    def create_top_bar(self):
        top_bar = QWidget()
        top_bar.setObjectName("topBar")

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Меню File.
        file_button = QToolButton()
        file_button.setText("File")
        file_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )

        file_menu = QMenu(file_button)
        file_menu.addAction("New")
        file_menu.addAction("Open")
        file_menu.addAction("Save")

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        file_button.setMenu(file_menu)

        # Кнопка включения режима редактирования.
        self.edit_button = QToolButton()
        self.edit_button.setText("Edit")
        self.edit_button.setCheckable(True)

        self.edit_button.toggled.connect(
            self.set_edit_mode
        )
        
                
        #Кнопка View
        view_button = QToolButton()
        view_button.setText("View")
        #self.edit_button.setCheckable(True)
        view_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )

        view_menu = QMenu(view_button)
        
        hand_action = view_menu.addAction("Hand")
        hand_action.triggered.connect(self.activate_hand_tool)
        
   
        rotate_menu = QMenu("Rotate", view_button)
        rotate_left_action = rotate_menu.addAction("Rotate Left")
        rotate_right_action = rotate_menu.addAction("Rotate Right")
        
        # Подключаем поворот рабочей области.
        rotate_left_action.triggered.connect(self.rotate_left)
        rotate_right_action.triggered.connect(self.rotate_right)
        view_menu.addMenu(rotate_menu)
        
        
        #view_menu.addAction("Zoom")
           
        zoom_menu = QMenu("Zoom", view_button)
        zoom_plus_action = zoom_menu.addAction("Zoom +")
        zoom_minus_action = zoom_menu.addAction("Zoom -")
        
        # Подключаем масштабирование рабочей области.
        zoom_plus_action.triggered.connect(self.zoom_in)
        zoom_minus_action.triggered.connect(self.zoom_out)
        view_menu.addMenu(zoom_menu)
        
        self.fit_all_action = view_menu.addAction("Fit All")
                              
        view_menu.addSeparator()

        view_button.setMenu(view_menu)

        layout.addWidget(file_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(view_button)
        layout.addStretch()

        return top_bar
    
    

    
    def create_side_panel(self):
        """Создаёт левую панель с вкладками и информацией об отрезке."""

        # Главный контейнер левой колонки.
        side_panel = QWidget()

        # Располагаем элементы вертикально:
        # сначала вкладки, затем информация.
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(5, 5, 5, 5)
        side_layout.setSpacing(8)

        # -------------------------------------------------
        # Вкладки построения и настроек.
        # -------------------------------------------------

        tabs = QTabWidget()

        # -------------------------------------------------
        # Вкладка построения отрезка.
        # -------------------------------------------------

        build_tab = QWidget()
        build_layout = QVBoxLayout(build_tab)

        form = QFormLayout()

        # Начальная точка задаётся в декартовых координатах.
        self.x1_input = QLineEdit("0")
        self.y1_input = QLineEdit("0")

        form.addRow("X₁:", self.x1_input)
        form.addRow("Y₁:", self.y1_input)

        # Выбор системы координат конечной точки.
        self.coordinate_mode = QComboBox()
        self.coordinate_mode.addItems(
            ["Декартовы", "Полярные"]
        )

        form.addRow(
            "Конечная точка:",
            self.coordinate_mode
        )

        self.x2_input = QLineEdit("3")
        self.y2_input = QLineEdit("4")

        self.x2_label = QLabel("X₂:")
        self.y2_label = QLabel("Y₂:")

        form.addRow(self.x2_label, self.x2_input)
        form.addRow(self.y2_label, self.y2_input)

        build_layout.addLayout(form)

        self.build_button = QPushButton("Построить отрезок")

        self.build_button.clicked.connect(
            self.create_segment
        )

        build_layout.addWidget(self.build_button)
        build_layout.addStretch()

        self.coordinate_mode.currentTextChanged.connect(
            self.update_coordinate_labels
        )

        # -------------------------------------------------
        # Вкладка настроек.
        # -------------------------------------------------

        settings_tab = QWidget()
        settings_layout = QFormLayout(settings_tab)

        # Единицы измерения угла.
        self.angle_unit_combo = QComboBox()
        self.angle_unit_combo.addItems(
            ["Градусы", "Радианы"]
        )

        settings_layout.addRow(
            "Единицы угла:",
            self.angle_unit_combo
        )

        # Настройка шага сетки.
        self.grid_step_input = QSpinBox()
        self.grid_step_input.setRange(1, 10)
        self.grid_step_input.setSingleStep(1)
        self.grid_step_input.setValue(1)

        settings_layout.addRow(
            "Шаг сетки:",
            self.grid_step_input
        )

        self.grid_step_input.valueChanged.connect(
            self.change_grid_step
        )

        # Обновляем информацию при изменении единиц угла.
        self.angle_unit_combo.currentTextChanged.connect(
            self.refresh_segment_info
        )

        # Цвет фона.
        self.background_color_button = QPushButton(
            "Выбрать цвет фона"
        )

        self.background_color_button.clicked.connect(
            self.choose_background_color
        )

        settings_layout.addRow(
            "Цвет фона:",
            self.background_color_button
        )

        # Цвет сетки.
        self.grid_color_button = QPushButton(
            "Выбрать цвет сетки"
        )

        self.grid_color_button.clicked.connect(
            self.choose_grid_color
        )

        settings_layout.addRow(
            "Цвет сетки:",
            self.grid_color_button
        )

        # Цвет отрезков.
        self.segment_color_button = QPushButton(
            "Выбрать цвет отрезков"
        )

        self.segment_color_button.clicked.connect(
            self.choose_segment_color
        )

        settings_layout.addRow(
            "Цвет отрезков:",
            self.segment_color_button
        )

        # Добавляем две вкладки.
        tabs.addTab(build_tab, "Построение")
        tabs.addTab(settings_tab, "Настройки")

        # Вкладки занимают свободное пространство.
        side_layout.addWidget(tabs, 1)

        # -------------------------------------------------
        # Нижняя информационная панель.
        # -------------------------------------------------

        info_panel = QGroupBox("Информация")
        info_layout = QVBoxLayout(info_panel)

        # Параметры текущего отрезка.
        self.point1_info = QLabel("Точка 1: —")
        self.point2_info = QLabel("Точка 2: —")
        self.length_info = QLabel("Длина: —")
        self.angle_info = QLabel("Угол: —")
        
        # Параметры текущего вида.
        self.cursor_info = QLabel("Координаты курсора: X: —, Y: —")
        self.zoom_info = QLabel("Масштаб: 1.00×")
        self.rotation_info = QLabel("Угол поворота: 0°")
        self.tool_info = QLabel("Активный инструмент: Нет")

        info_layout.addWidget(self.point1_info)
        info_layout.addWidget(self.point2_info)
        info_layout.addWidget(self.length_info)
        info_layout.addWidget(self.angle_info)
        
        # Информация о рабочей области.
        info_layout.addSpacing(10)

        info_layout.addWidget(self.cursor_info)
        info_layout.addWidget(self.zoom_info)
        info_layout.addWidget(self.rotation_info)
        info_layout.addWidget(self.tool_info)

        # Добавляем информационную панель внизу.
        side_layout.addWidget(info_panel)

        return side_panel

    # -------------------------------------------------
    # Координаты
    # -------------------------------------------------

    def update_coordinate_labels(self, mode):
        """Меняет подписи полей конечной точки."""

        if mode == "Полярные":
            self.x2_label.setText("r₂:")
            self.y2_label.setText("θ₂:")
        else:
            self.x2_label.setText("X₂:")
            self.y2_label.setText("Y₂:")

    def change_grid_step(self, value):
        """Изменяет шаг сетки рабочей области."""

        self.drawing_area.grid_step = value
        self.drawing_area.update()

    # -------------------------------------------------
    # Выбор цветов
    # -------------------------------------------------

    def choose_background_color(self):
        """Открывает диалог выбора цвета фона."""

        color = QColorDialog.getColor(
            QColor(self.drawing_area.background_color),
            self,
            "Выбор цвета фона",
        )

        # Если пользователь отменил выбор,
        # оставляем прежний цвет.
        if not color.isValid():
            return

        self.drawing_area.background_color = color.name()

        self.update_color_buttons()
        self.drawing_area.update()

    def choose_grid_color(self):
        """Открывает диалог выбора цвета сетки."""

        color = QColorDialog.getColor(
            QColor(self.drawing_area.grid_color),
            self,
            "Выбор цвета сетки",
        )

        if not color.isValid():
            return

        self.drawing_area.grid_color = color.name()

        # Обновляем и основные линии сетки.
        self.drawing_area.major_grid_color = color.name()

        self.update_color_buttons()
        self.drawing_area.update()

    def choose_segment_color(self):
        """Открывает диалог выбора цвета отрезков."""

        color = QColorDialog.getColor(
            QColor(self.drawing_area.segment_color),
            self,
            "Выбор цвета отрезков",
        )

        if not color.isValid():
            return

        self.drawing_area.segment_color = color.name()

        self.update_color_buttons()
        self.drawing_area.update()

    def update_color_buttons(self):
        """Показывает текущие цвета на кнопках."""

        self.background_color_button.setStyleSheet(
            "QPushButton { "
            f"background-color: "
            f"{self.drawing_area.background_color}; "
            "}"
        )

        self.grid_color_button.setStyleSheet(
            "QPushButton { "
            f"background-color: "
            f"{self.drawing_area.grid_color}; "
            "}"
        )

        self.segment_color_button.setStyleSheet(
            "QPushButton { "
            f"background-color: "
            f"{self.drawing_area.segment_color}; "
            "}"
        )

    # -------------------------------------------------
    # Построение отрезка
    # -------------------------------------------------


    def create_segment(self):
        """Создаёт отрезок по декартовым или полярным координатам."""

        try:
            # Считываем координаты начальной точки.
            x1 = float(
                self.x1_input.text().strip().replace(",", ".")
            )
            y1 = float(
                self.y1_input.text().strip().replace(",", ".")
            )

            # Считываем значения конечной точки.
            value1 = float(
                self.x2_input.text().strip().replace(",", ".")
            )
            value2 = float(
                self.y2_input.text().strip().replace(",", ".")
            )

            # По умолчанию исходного полярного угла нет.
            input_angle = None
            input_angle_degrees = None

            if self.coordinate_mode.currentText() == "Полярные":
                radius = value1
                theta = value2

                if radius < 0:
                    raise ValueError(
                        "Радиус не может быть отрицательным"
                    )

                # Определяем единицу ввода угла.
                degrees = (
                    self.angle_unit_combo.currentText()
                    == "Градусы"
                )

                # Строим конечную точку относительно начальной.
                x2, y2 = polar_to_cartesian(
                    radius,
                    theta,
                    degrees=degrees,
                    x1=x1,
                    y1=y1,
                )

                # Сохраняем исходный угол пользователя.
                input_angle = theta
                input_angle_degrees = degrees

            else:
                # При декартовом вводе конечная точка задана напрямую.
                x2 = value1
                y2 = value2

            # Создаём геометрические объекты.
            point1 = Point(x1, y1)
            point2 = Point(x2, y2)

            segment = Segment(
                point1,
                point2,
                input_angle=input_angle,
                input_angle_degrees=input_angle_degrees,
            )

            # Добавляем отрезок на рабочую область.
            self.drawing_area.add_segment(segment)

            # Обновляем информацию.
            self.update_segment_info(segment)

        except (ValueError, TypeError) as error:
            QMessageBox.warning(
                self,
                "Ошибка ввода",
                f"Проверьте введённые координаты.\n{error}",
            )

    def update_segment_info(self, segment):
        """Отображает координаты, длину и угол отрезка."""

        self.current_segment = segment

        start = segment.start
        end = segment.end

        self.point1_info.setText(
            f"Точка 1: ({start.x:.3f}, {start.y:.3f})"
        )

        self.point2_info.setText(
            f"Точка 2: ({end.x:.3f}, {end.y:.3f})"
        )

        self.length_info.setText(
            f"Длина: {segment.length:.3f}"
        )

        # Если отрезок задан полярными координатами,
        # показываем исходный угол пользователя первым.
        if segment.input_angle is not None:
            angle = segment.input_angle

            if segment.input_angle_degrees:
                degrees = angle
                radians = math.radians(angle)

                angle_text = (
                    f"{degrees:.3f}° ({radians:.3f} рад)"
                )
            else:
                radians = angle
                degrees = math.degrees(angle)

                angle_text = (
                    f"{radians:.3f} рад ({degrees:.3f}°)"
                )

        else:
            # Если угол не вводили, например при построении
            # по декартовым координатам или мышью,
            # вычисляем его по геометрии отрезка.
            radians = segment.angle
            degrees = math.degrees(radians)

            # В этом случае первой показываем единицу,
            # выбранную в настройках.
            if self.angle_unit_combo.currentText() == "Градусы":
                angle_text = (
                    f"{degrees:.3f}° ({radians:.3f} рад)"
                )
            else:
                angle_text = (
                    f"{radians:.3f} рад ({degrees:.3f}°)"
                )

        self.angle_info.setText(f"Угол: {angle_text}")


    def refresh_segment_info(self, *_):
        """Обновляет угол при изменении единицы измерения."""

        if self.current_segment is not None:
            self.update_segment_info(
                self.current_segment
            )

    def update_info_after_deletion(self):
        """Обновляет информацию после удаления отрезка."""

        if self.drawing_area.segments:
            # Показываем последний оставшийся отрезок.
            segment = self.drawing_area.segments[-1]
            self.update_segment_info(segment)
        else:
            # Если отрезков больше нет, очищаем информацию.
            self.current_segment = None

            self.point1_info.setText("Точка 1: —")
            self.point2_info.setText("Точка 2: —")
            self.length_info.setText("Длина: —")
            self.angle_info.setText("Угол: —")

    # -------------------------------------------------
    # Режим редактирования
    # -------------------------------------------------

    # def set_edit_mode(self, enabled):
    #     """Включает или выключает режим редактирования."""

    #     # Передаём изменение режима контроллеру.
    #     self.controller.set_edit_mode(enabled)

    #     # Показываем или скрываем панель инструментов.
    #     self.tool_panel.setVisible(enabled)

    #     # Передаём текущий инструмент рабочей области.
    #     self.drawing_area.set_tool(
    #         self.controller.current_tool
    #     )
    #     self.update_active_tool_info()
    
    def set_edit_mode(self, enabled):
        """Включает или выключает режим редактирования."""

        self.controller.set_edit_mode(enabled)

        self.tool_panel.setVisible(enabled)

        if enabled:
            selected_tool = self.tool_panel.get_current_tool()

            if selected_tool is None:
                selected_tool = "segment"
                self.tool_panel.set_current_tool(selected_tool)

            self.controller.set_tool(selected_tool)
            print("После синхронизации:", self.controller.current_tool)

        self.drawing_area.set_tool(
            self.controller.current_tool
        )

        self.update_active_tool_info()
        
        print("Кнопка в панели:", selected_tool)
        print("Инструмент контроллера:", self.controller.current_tool)
        print("Режим редактирования:", self.controller.is_editing)

    # -------------------------------------------------
    # Режим перемещения рукой рабочей области
    # -------------------------------------------------
    def activate_hand_tool(self):
        """Включает или выключает инструмент Hand."""

        # Проверяем, выбран ли уже Hand.
        if self.controller.current_view_tool == "hand":

            # Если выбран, отключаем.
            self.controller.set_view_tool(None)

        else:
            # Если не выбран, активируем.
            self.controller.set_view_tool("hand")

        # Передаём актуальное состояние навигации в DrawingArea.
        self.drawing_area.set_navigation_tool(
            self.controller.current_view_tool
        )
        self.navigation_panel.set_hand_active(
            self.controller.current_view_tool == "hand"
        )
        self.update_active_tool_info()
            
    def activate_edit_tool(self, tool_name):
        """Активирует инструмент редактирования."""

        # Проверяем возможность выбора инструмента.
        if self.controller.set_tool(tool_name):

            # Отключаем инструмент навигации.
            self.controller.set_view_tool(None)
            self.drawing_area.set_navigation_tool(None)

            # Передаём инструмент рабочей области.
            self.drawing_area.set_tool(tool_name)
        self.update_active_tool_info()
            
    def rotate_left(self):
        self.drawing_area.rotate_view(-15)

    def rotate_right(self):
        self.drawing_area.rotate_view(15)
        
    def rotate_left_90(self):
        self.drawing_area.rotate_view(-90)

    def rotate_right_90(self):
        self.drawing_area.rotate_view(90)
        
    def snap_left(self):
        self.drawing_area.snap_rotation(-1)

    def snap_right(self):
        self.drawing_area.snap_rotation(1)
        
    def zoom_in(self):
        self.drawing_area.zoom_view(1.15)


    def zoom_out(self):
        self.drawing_area.zoom_view(1 / 1.15)


    def create_shortcuts(self):
        """Создаёт горячие клавиши для поворота рабочей области."""

        # Поворот налево на 15 градусов.
        self.rotate_left_shortcut = QShortcut(
            QKeySequence("Left"), self
        )
        self.rotate_left_shortcut.activated.connect(self.rotate_left)

        # Поворот направо на 15 градусов.
        self.rotate_right_shortcut = QShortcut(
            QKeySequence("Right"), self
        )
        self.rotate_right_shortcut.activated.connect(self.rotate_right)

        # Поворот налево на 90 градусов.
        self.rotate_left_90_shortcut = QShortcut(
            QKeySequence("Shift+Alt+Left"), self
        )
        self.rotate_left_90_shortcut.activated.connect(self.rotate_left_90)

        # Поворот направо на 90 градусов.
        self.rotate_right_90_shortcut = QShortcut(
            QKeySequence("Shift+Alt+Right"), self
        )
        self.rotate_right_90_shortcut.activated.connect(self.rotate_right_90)
        
        # Привязка налево к углу 90°.
        self.rotate_left_90_shortcut = QShortcut(
            QKeySequence("Shift+Left"), self
        )
        self.rotate_left_90_shortcut.activated.connect(self.snap_left)

        # Привязка направо к углу 90°.
        self.rotate_right_90_shortcut = QShortcut(
            QKeySequence("Shift+Right"), self
        )
        self.rotate_right_90_shortcut.activated.connect(self.snap_right)
        
        self.zoom_in_shortcut = QShortcut(
            QKeySequence("Ctrl++"), self
        )
        self.zoom_in_shortcut.activated.connect(self.zoom_in)

        self.zoom_out_shortcut = QShortcut(
            QKeySequence("Ctrl+-"), self
        )
        self.zoom_out_shortcut.activated.connect(self.zoom_out)
        
    def reset_view(self):
        """Возвращает рабочую область к исходному виду."""

        self.drawing_area.zoom = 1.0
        self.drawing_area.view_rotation = 0.0

        self.drawing_area.origin_x = (
            self.drawing_area.width() / 2
        )
        self.drawing_area.origin_y = (
            self.drawing_area.height() / 2
        )

        self.drawing_area.update()
        self.drawing_area.view_changed.emit()
        
    def update_cursor_info(self, x, y):
        """Отображает мировые координаты курсора."""

        self.cursor_info.setText(
            f"Координаты курсора: X: {x:.3f}, Y: {y:.3f}"
        )


    def update_view_info(self):
        """Обновляет масштаб и угол поворота."""

        self.zoom_info.setText(
            f"Масштаб: {self.drawing_area.zoom:.2f}×"
        )

        self.rotation_info.setText(
            f"Угол поворота: {self.drawing_area.view_rotation:.1f}°"
        )


    def update_active_tool_info(self):
        """Отображает название активного инструмента."""

        if self.controller.current_view_tool == "hand":
            tool_name = "Рука"

        elif self.controller.current_tool == "segment":
            tool_name = "Отрезок"

        elif self.controller.current_tool == "delete":
            tool_name = "Удаление"

        else:
            tool_name = "Нет"

        self.tool_info.setText(
            f"Активный инструмент: {tool_name}"
        )