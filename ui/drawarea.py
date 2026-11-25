from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget, QMenu

from geometry.point import Point
from geometry.segment import Segment
import math


class DrawingArea(QWidget):
    """Рабочая область для построения и удаления отрезков."""

    # Сигнал отправляется после создания отрезка.
    segment_created = Signal(object)

    # Сигнал отправляется после удаления отрезка.
    segment_deleted = Signal()
    
    # Изменение мировых координат курсора.
    cursor_position_changed = Signal(float, float)

    # Изменение масштаба или угла поворота.
    view_changed = Signal()

    # Запрос на включение инструмента «Рука».
    hand_tool_requested = Signal()

    # Запрос на сброс вида.
    reset_view_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Цвет фона рабочей области.
        self.background_color = "#F5F7FA"

        # Цвет обычных линий сетки.
        self.grid_color = "#DDE2E8"

        # Цвет основных линий сетки.
        self.major_grid_color = "#C5CDD6"

        # Цвет координатных осей.
        self.axis_color = "#64748B"

        # Цвет отрезков.
        self.segment_color = "#E63946"

        # Цвет предварительного отрезка.
        self.preview_color = "#2563EB"

        # Расстояние между линиями сетки в пикселях.
        # Масштаб: количество пикселей на одну координатную единицу.
        self.pixels_per_unit = 25

        # Расстояние между линиями сетки в координатных единицах.
        self.grid_step = 1

        # Масштабирование рабочей области.
        self.zoom = 1.0
        
        # Текущий угол поворота рабочей области в градусах.
        self.view_rotation = 0.0

        # Начало координат на экране.
        self.origin_x = None
        self.origin_y = None

        # Список созданных отрезков.
        self.segments = []

        # Название активного инструмента.
        self.current_tool = None
        
        # Активный инструмент навигации.
        self.navigation_tool = None

        # Первая точка при построении мышью.
        self.start_point = None

        # Текущая позиция курсора для предпросмотра.
        self.mouse_position = None

        # Состояние перемещения рабочей области.
        self.is_panning = False
        self.last_mouse_pos = None
        
        # Кнопка, которой началось перемещение.
        self.pan_button = None

        # Минимальный размер рабочей области.
        self.setMinimumSize(400, 300)

        # Получаем события движения мыши, даже без нажатия кнопки.
        self.setMouseTracking(True)
        

    def set_tool(self, tool_name):
        """Устанавливает активный инструмент."""

        self.current_tool = tool_name

        # При переключении инструмента отменяем незавершённый отрезок.
        self.start_point = None
        self.mouse_position = None
        
        if self.navigation_tool == "hand":
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif tool_name == "segment":
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        self.update()
        
    def set_navigation_tool(self, tool_name):
        """Устанавливает инструмент навигации."""

        self.navigation_tool = tool_name

        # Отменяем незавершённое построение отрезка.
        self.start_point = None
        self.mouse_position = None

        if tool_name == "hand":
            self.setCursor(Qt.CursorShape.OpenHandCursor)

        elif self.current_tool == "segment":
            self.setCursor(Qt.CursorShape.CrossCursor)

        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        self.update()

    # def add_segment(self, segment):
    #     """Добавляет готовый отрезок на рабочую область."""

    #     if not isinstance(segment, Segment):
    #         raise TypeError("Ожидался объект Segment")

    #     self.segments.append(segment)
    #     self.update()
    
    def add_segment(self, segment):
        if not isinstance(segment, Segment):
            raise TypeError("Ожидался объект Segment")

        self.segments.append(segment)

        print("Вызван add_segment()")
        print("Список отрезков:", self.segments)

        self.update()


    def paintEvent(self, event):
        """Перерисовывает рабочую область с учётом поворота."""

        painter = QPainter(self)

        try:
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing
            )

            # Рисуем фон. Он не должен поворачиваться.
            painter.fillRect(
                self.rect(),
                QColor(self.background_color)
            )

            # При первом отображении помещаем начало координат в центр.
            if self.origin_x is None or self.origin_y is None:
                self.origin_x = self.width() / 2
                self.origin_y = self.height() / 2

            # Сохраняем исходное состояние Painter.
            painter.save()

            # Определяем центр рабочей области.
            center_x = self.width() / 2
            center_y = self.height() / 2

            # Переносим начало системы координат в центр.
            painter.translate(center_x, center_y)

            # Поворачиваем систему координат.
            painter.rotate(self.view_rotation)

            # Возвращаем начало системы координат обратно.
            painter.translate(-center_x, -center_y)

            # Рисуем все элементы в единой системе координат.
            self.draw_grid(
                painter,
                self.origin_x,
                self.origin_y
            )

            self.draw_axes(
                painter,
                self.origin_x,
                self.origin_y
            )

            self.draw_segments(painter)
            self.draw_preview(painter)

            # Возвращаем исходное состояние Painter.
            painter.restore()

        finally:
            if painter.isActive():
                painter.end()


    def draw_grid(self, painter, origin_x, origin_y):
        """Рисует масштабируемую координатную сетку."""

        step = (
            self.grid_step
            * self.pixels_per_unit
            * self.zoom
        )

        if step <= 0:
            return

        # Определяем запас, достаточный для покрытия углов.
        radius = math.hypot(
            self.width(),
            self.height()
        )

        left = -radius
        right = self.width() + radius
        top = -radius
        bottom = self.height() + radius

        # Номера крайних линий по горизонтали.
        first_column = int((left - origin_x) // step) - 1
        last_column = int((right - origin_x) // step) + 1

        # Номера крайних линий по вертикали.
        first_row = int((top - origin_y) // step) - 1
        last_row = int((bottom - origin_y) // step) + 1

        # Вертикальные линии.
        for i in range(first_column, last_column + 1):
            x = origin_x + i * step

            color = (
                self.major_grid_color
                if i % 5 == 0
                else self.grid_color
            )

            painter.setPen(QPen(QColor(color), 1))

            painter.drawLine(
                round(x), round(top),
                round(x), round(bottom)
            )

        # Горизонтальные линии.
        for i in range(first_row, last_row + 1):
            y = origin_y + i * step

            color = (
                self.major_grid_color
                if i % 5 == 0
                else self.grid_color
            )

            painter.setPen(QPen(QColor(color), 1))

            painter.drawLine(
                round(left), round(y),
                round(right), round(y)
            )
        
    def draw_axes(self, painter, origin_x, origin_y):
        """Рисует оси X и Y и начало координат."""

        painter.setPen(
            QPen(QColor(self.axis_color), 2)
        )

        # Вычисляем длину осей, достаточную для покрытия экрана при повороте.
        #radius = math.hypot(self.width(), self.height())
        # Расстояние от начала координат до центра рабочей области.
        distance_to_center = math.hypot(
            origin_x - self.width() / 2,
            origin_y - self.height() / 2
        )

        # Радиус, достаточный для покрытия всей рабочей области.
        radius = distance_to_center + math.hypot(
            self.width(), self.height()
        ) / 2

        # Ось X.
        painter.drawLine(
            round(origin_x - radius), round(origin_y),
            round(origin_x + radius), round(origin_y)
        )

        # Ось Y.
        painter.drawLine(
            round(origin_x), round(origin_y - radius),
            round(origin_x), round(origin_y + radius)
        )

        # Подписи осей.
        painter.drawText(
            self.width() - 22,
            round(origin_y) - 8,
            "X"
        )

        painter.drawText(
            round(origin_x) + 8,
            18,
            "Y"
        )

        # Маркер начала координат.
        painter.setBrush(QColor(self.axis_color))

        painter.drawEllipse(
            round(origin_x) - 4,
            round(origin_y) - 4,
            8,
            8
        )

        painter.drawText(
            round(origin_x) + 9,
            round(origin_y) + 18,
            "O (0, 0)"
        )
    def rotate_screen_point(self, x, y, angle):
        """Логика Rotate.Поворачивает экранную точку вокруг центра рабочей области."""

        # Находим геометрический центр рабочей области.
        center_x = self.width() / 2
        center_y = self.height() / 2

        # Переводим координаты точки относительно центра.
        dx = x - center_x
        dy = y - center_y

        # Переводим угол из градусов в радианы.
        angle_rad = math.radians(angle)

        # Вычисляем координаты после поворота.
        rotated_x = (
            center_x
            + dx * math.cos(angle_rad)
            - dy * math.sin(angle_rad)
        )

        rotated_y = (
            center_y
            + dx * math.sin(angle_rad)
            + dy * math.cos(angle_rad)
        )

        return rotated_x, rotated_y
    
    def world_to_screen(self, point):
        """Преобразует координаты чертежа в экранные."""
        scale = self.pixels_per_unit * self.zoom
        #self.origin_x экранная координата
        #point.x * scale смещение оси в пикселях
        x = self.origin_x + point.x * scale
        y = self.origin_y - point.y * scale

        return x, y


    def screen_to_world(self, x, y):
        """Преобразует экранные координаты в мировые."""

        # Отменяем поворот рабочей области.
        x, y = self.rotate_screen_point(
            x,
            y,
            -self.view_rotation
        )

        # Вычисляем масштаб.
        scale = self.pixels_per_unit * self.zoom

        # Переводим экранные координаты в мировые.
        world_x = (x - self.origin_x) / scale
        world_y = (self.origin_y - y) / scale

        return Point(world_x, world_y)


    def draw_segments(self, painter):
        """Отображает все созданные отрезки."""
        
        print("Вызван draw_segments(), количество:", len(self.segments))

        pen = QPen(
            QColor(self.segment_color),
            2,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap
        )

        painter.setPen(pen)

        for segment in self.segments:
            # Переводим обе точки в экранные координаты.
            x1, y1 = self.world_to_screen(segment.start)
            x2, y2 = self.world_to_screen(segment.end)

            painter.drawLine(
                round(x1),
                round(y1),
                round(x2),
                round(y2)
            )

    def draw_preview(self, painter):
        """Рисует предварительный отрезок до второго щелчка."""

        if (
            self.current_tool != "segment"
            or self.start_point is None
            or self.mouse_position is None
        ):
            return

        # Начало предварительного отрезка.
        x1, y1 = self.world_to_screen(self.start_point)

        # Конец следует за курсором мыши.
        
        # Отменяем поворот координат курсора.
        x2, y2 = self.rotate_screen_point(
            self.mouse_position.x(),
            self.mouse_position.y(),
            -self.view_rotation
        )

        pen = QPen(
            QColor(self.preview_color),
            2,
            Qt.PenStyle.DashLine
        )

        painter.setPen(pen)

        painter.drawLine(
            round(x1),
            round(y1),
            round(x2),
            round(y2)
        )

    def mousePressEvent(self, event):
        """Обрабатывает щелчки мыши."""

        # Средняя кнопка мыши работает всегда.
        # Левая кнопка работает при выбранном Hand.
        if (
            event.button() == Qt.MouseButton.MiddleButton
            or (
                event.button() == Qt.MouseButton.LeftButton
                and self.navigation_tool == "hand"
            )
        ):
            self.is_panning = True
            self.last_mouse_pos = event.position()
            self.pan_button = event.button()

            self.setCursor(
                Qt.CursorShape.ClosedHandCursor
            )

            event.accept()
            return

        # Инструменты реагируют только на левую кнопку.
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        

        # -----------------------------------------------
        # Инструмент «Отрезок».
        # -----------------------------------------------
        if self.current_tool == "segment":
            point = self.screen_to_world(
                event.position().x(),
                event.position().y()
            )

            if self.start_point is None:
                # Первый щелчок задаёт начальную точку.
                self.start_point = point
                self.mouse_position = event.position()
            else:
                # Второй щелчок задаёт конечную точку.
                segment = Segment(
                    self.start_point,
                    point
                )

                self.add_segment(segment)

                # Сбрасываем состояние построения.
                self.start_point = None
                self.mouse_position = None

                # Сообщаем главному окну о новом отрезке.
                self.segment_created.emit(segment)

            self.update()
            event.accept()
            return

        # -----------------------------------------------
        # Инструмент «Удалить».
        # -----------------------------------------------
        if self.current_tool == "delete":
            deleted = self.delete_segment_at(
                event.position().x(),
                event.position().y()
            )

            if deleted:
                self.segment_deleted.emit()

            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Обрабатывает движение мыши и перемещение рабочей области."""

        # Перемещение рабочей области.
        if (
            self.is_panning
            and self.last_mouse_pos is not None
        ):
            # Вычисляем смещение курсора с предыдущего события.
            delta = event.position() - self.last_mouse_pos

            # Переводим смещение в систему координат до поворота.
            angle_rad = math.radians(-self.view_rotation)

            delta_x = (
                delta.x() * math.cos(angle_rad)
                - delta.y() * math.sin(angle_rad)
            )

            delta_y = (
                delta.x() * math.sin(angle_rad)
                + delta.y() * math.cos(angle_rad)
            )

            # Перемещаем начало координат.
            self.origin_x += delta_x
            self.origin_y += delta_y
            
            # Передаём мировые координаты курсора.
            world_point = self.screen_to_world(
                event.position().x(),
                event.position().y()
            )

            self.cursor_position_changed.emit(
                world_point.x,
                world_point.y
            )

                        # Запоминаем новую позицию курсора.
            self.last_mouse_pos = event.position()

            self.update()
            event.accept()
            return

        # Обновляем предварительный отрезок вслед за курсором.
        if (
            self.current_tool == "segment"
            and self.start_point is not None
        ):
            self.mouse_position = event.position()
            self.update()
            
        # Передаём мировые координаты курсора.
        world_point = self.screen_to_world(
            event.position().x(),
            event.position().y()
        )

        self.cursor_position_changed.emit(
            world_point.x,
            world_point.y
        )

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Завершает перемещение рабочей области."""

        # Проверяем, отпущена ли кнопка, которой начали перемещение.
        if (
            self.is_panning
            and event.button() == self.pan_button
        ):
            self.is_panning = False
            self.last_mouse_pos = None
            self.pan_button = None

            # Возвращаем курсор в зависимости от активного инструмента.
            if self.navigation_tool == "hand":
                self.setCursor(Qt.CursorShape.OpenHandCursor)

            elif self.current_tool == "segment":
                self.setCursor(Qt.CursorShape.CrossCursor)

            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

            event.accept()
            return

        super().mouseReleaseEvent(event)


    def delete_segment_at(self, mouse_x, mouse_y):
        """Удаляет ближайший к курсору отрезок."""

        # Переводим координаты курсора обратно в систему
        # координат до поворота вида.
        mouse_x, mouse_y = self.rotate_screen_point(
            mouse_x,
            mouse_y,
            -self.view_rotation
        )

        # Допустимое расстояние от курсора до отрезка.
        tolerance = 8

        nearest_segment = None
        nearest_distance = float("inf")

        # Ищем ближайший отрезок.
        for segment in self.segments:
            x1, y1 = self.world_to_screen(segment.start)
            x2, y2 = self.world_to_screen(segment.end)

            distance = self.point_to_segment_distance(
                mouse_x,
                mouse_y,
                x1,
                y1,
                x2,
                y2
            )

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_segment = segment

        # Удаляем объект, только если курсор достаточно близко.
        if (
            nearest_segment is not None
            and nearest_distance <= tolerance
        ):
            self.segments.remove(nearest_segment)
            self.update()
            return True

        return False


    @staticmethod
    def point_to_segment_distance(
        px, py, x1, y1, x2, y2
    ):
        """Вычисляет расстояние от курсора до отрезка."""

        dx = x2 - x1
        dy = y2 - y1

        length_squared = dx * dx + dy * dy

        # Если отрезок вырожден в точку.
        if length_squared == 0:
            return (
                (px - x1) ** 2 + (py - y1) ** 2
            ) ** 0.5

        # Находим положение ближайшей точки на отрезке.
        t = (
            (px - x1) * dx + (py - y1) * dy
        ) / length_squared

        # Ограничиваем точку концами отрезка.
        t = max(0.0, min(1.0, t))

        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        # Возвращаем расстояние от курсора до ближайшей точки.
        return (
            (px - closest_x) ** 2
            + (py - closest_y) ** 2
        ) ** 0.5
        
    #self — обращение к текущему объекту DrawingArea.
    #factor — коэффициент изменения масштаба.
    #center_x — координата X точки, относительно которой масштабируем.
    #center_y — координата Y этой точки.
    def zoom_view(self, factor, center_x=None, center_y=None): #получает координаты курсора
        """Изменяет масштаб рабочей области относительно заданной точки."""
        #проверяем если центр рабочей области
        if self.origin_x is None or self.origin_y is None:
            self.origin_x = self.width() / 2
            self.origin_y = self.height() / 2

        # Если точка масштабирования не задана,
        # используем центр рабочей области.
        if center_x is None or center_y is None:
            center_x = self.width() / 2
            center_y = self.height() / 2

        # Учитываем поворот рабочей области.
        mouse_x, mouse_y = self.rotate_screen_point(
            center_x,
            center_y,
            -self.view_rotation
        )

        # Ограничиваем масштаб.
        new_zoom = max(0.1, min(5.0, self.zoom * factor))

        if new_zoom == self.zoom:
            return

        actual_factor = new_zoom / self.zoom

        # Компенсируем смещение относительно точки масштабирования.
        self.origin_x = (
            mouse_x - (mouse_x - self.origin_x) * actual_factor
        )

        self.origin_y = (
            mouse_y - (mouse_y - self.origin_y) * actual_factor
        )

        self.zoom = new_zoom
        self.update()
        self.view_changed.emit()
        
    def wheelEvent(self, event):
        """Обрабатывает прокручивание: перемещение или масштабирование."""

        if self.origin_x is None or self.origin_y is None:
            self.origin_x = self.width() / 2
            self.origin_y = self.height() / 2

        # Если выбран Hand, прокручивание перемещает рабочую область.
        if self.navigation_tool == "hand":

            # Получаем смещение от тачпада или колёсика.
            delta = event.pixelDelta()

            # Если пиксельного смещения нет, используем угловое.
            if delta.isNull():
                delta = event.angleDelta() / 2

            # Перемещаем рабочую область.
            self.origin_x += delta.x()
            self.origin_y += delta.y()

            self.update()
            self.view_changed.emit()
            event.accept()
            return

        # Если Hand не выбран, выполняем масштабирование.
        if event.angleDelta().y() > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15

        # Масштабируем относительно положения курсора.
        self.zoom_view(
            factor,
            event.position().x(),
            event.position().y()
        )

        event.accept()
        
    def rotate_view(self, angle):
        """Непосредственно функция Rotate. Поворачивает рабочую область на заданный угол."""

        # Изменяем текущий угол поворота.
        self.view_rotation += angle

        # Ограничиваем значение угла диапазоном от 0 до 360.
        self.view_rotation %= 360

        # Запрашиваем перерисовку рабочей области.
        self.update()
        self.view_changed.emit()
    
    def snap_rotation(self, direction):
        """Привязывает угол поворота к ближайшему углу 90° с учётом направления."""

        # Получаем текущий угол в диапазоне от 0 до 360°.
        angle = self.view_rotation % 360

        # Поворот направо — к следующему углу, кратному 90°.
        if direction > 0:
            target_angle = (math.floor(angle / 90) + 1) * 90

        # Поворот налево — к предыдущему углу, кратному 90°.
        else:
            target_angle = (math.ceil(angle / 90) - 1) * 90

        self.view_rotation = target_angle % 360
        self.update()
        
    # def keyPressEvent(self, event):
    #     """Обрабатывает нажатие клавиш."""

    #     if event.key() == Qt.Key.Key_Shift:
    #         self.snap_rotation()

    #     else:
    #         super().keyPressEvent(event)


    # def keyReleaseEvent(self, event):
    #     """Обрабатывает отпускание клавиш."""

    #     super().keyReleaseEvent(event)
    def fit_all(self):
        """Подбирает масштаб и положение для отображения всех отрезков."""

        # Если отрезков нет, ничего не делаем.
        if not self.segments:
            return

        # Собираем все точки отрезков.
        points = []

        for segment in self.segments:
            points.append(segment.start)
            points.append(segment.end)

        # Находим границы чертежа.
        min_x = min(point.x for point in points)
        max_x = max(point.x for point in points)

        min_y = min(point.y for point in points)
        max_y = max(point.y for point in points)

        # Находим центр чертежа.
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Переводим угол поворота в радианы.
        angle = math.radians(self.view_rotation)

        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)

        # Определяем границы чертежа с учётом поворота.
        rotated_points = []

        for point in points:

            dx = point.x - center_x
            dy = -(point.y - center_y)

            rotated_x = dx * cos_angle - dy * sin_angle
            rotated_y = dx * sin_angle + dy * cos_angle

            rotated_points.append((rotated_x, rotated_y))

        # Находим ширину и высоту повёрнутого чертежа.
        min_rotated_x = min(point[0] for point in rotated_points)
        max_rotated_x = max(point[0] for point in rotated_points)

        min_rotated_y = min(point[1] for point in rotated_points)
        max_rotated_y = max(point[1] for point in rotated_points)

        drawing_width = max_rotated_x - min_rotated_x
        drawing_height = max_rotated_y - min_rotated_y

        # Оставляем отступы от краёв рабочей области.
        margin = 60

        available_width = self.width() - 2 * margin
        available_height = self.height() - 2 * margin

        # Вычисляем подходящий масштаб.
        zoom_values = []

        if drawing_width > 0:
            zoom_values.append(
                available_width / (drawing_width * self.pixels_per_unit)
            )

        if drawing_height > 0:
            zoom_values.append(
                available_height / (drawing_height * self.pixels_per_unit)
            )

        # Если все точки совпадают, сохраняем текущий масштаб.
        if zoom_values:
            new_zoom = min(zoom_values)
        else:
            new_zoom = self.zoom

        # Учитываем допустимые пределы масштаба.
        self.zoom = max(0.01, min(5.0, new_zoom))

        # Центрируем чертёж.
        self.origin_x = (
            self.width() / 2
            - center_x * self.pixels_per_unit * self.zoom
        )

        self.origin_y = (
            self.height() / 2
            + center_y * self.pixels_per_unit * self.zoom
        )

        # Обновляем отображение.
        self.update()
        
    def contextMenuEvent(self, event):
        """Создаёт контекстное меню навигации."""

        menu = QMenu(self)

        # Масштабирование.
        zoom_in_action = menu.addAction("Увеличить масштаб")
        zoom_out_action = menu.addAction("Уменьшить масштаб")

        menu.addSeparator()

        # Перемещение и отображение чертежа.
        hand_action = menu.addAction("Рука")
        fit_all_action = menu.addAction("Показать всё")
        reset_action = menu.addAction("Сбросить вид")

        menu.addSeparator()

        # Поворот рабочей области.
        rotate_left_action = menu.addAction("Повернуть влево")
        rotate_right_action = menu.addAction("Повернуть вправо")

        # Подключаем команды.
        zoom_in_action.triggered.connect(
            lambda: self.zoom_view(1.15)
        )

        zoom_out_action.triggered.connect(
            lambda: self.zoom_view(1 / 1.15)
        )

        hand_action.triggered.connect(
            self.hand_tool_requested.emit
        )

        fit_all_action.triggered.connect(self.fit_all)

        reset_action.triggered.connect(
            self.reset_view_requested.emit
        )

        rotate_left_action.triggered.connect(
            lambda: self.rotate_view(-15)
        )

        rotate_right_action.triggered.connect(
            lambda: self.rotate_view(15)
        )

        # Показываем меню в месте нажатия ПКМ.
        menu.exec(event.globalPos())