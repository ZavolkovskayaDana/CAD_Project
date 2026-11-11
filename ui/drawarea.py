from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget

from geometry.point import Point
from geometry.segment import Segment


class DrawingArea(QWidget):
    """Рабочая область для построения и удаления отрезков."""

    # Сигнал отправляется после создания отрезка.
    segment_created = Signal(object)

    # Сигнал отправляется после удаления отрезка.
    segment_deleted = Signal()

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

        # Начало координат на экране.
        self.origin_x = None
        self.origin_y = None

        # Список созданных отрезков.
        self.segments = []

        # Название активного инструмента.
        self.current_tool = None

        # Первая точка при построении мышью.
        self.start_point = None

        # Текущая позиция курсора для предпросмотра.
        self.mouse_position = None

        # Состояние перемещения рабочей области.
        self.is_panning = False
        self.last_mouse_pos = None

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

        if tool_name == "segment":
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
        """Перерисовывает рабочую область."""

        painter = QPainter(self)

        try:
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing
            )

            painter.fillRect(
                self.rect(),
                QColor(self.background_color)
            )

            # При первом отображении помещаем начало координат в центр.
            if self.origin_x is None or self.origin_y is None:
                self.origin_x = self.width() / 2
                self.origin_y = self.height() / 2

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

        finally:
            if painter.isActive():
                painter.end()


    def draw_grid(self, painter, origin_x, origin_y):
        """Рисует масштабируемую координатную сетку."""

        #step = self.grid_step * self.zoom
        step = (
            self.grid_step
            * self.pixels_per_unit
            * self.zoom
        )

        if step <= 0:
            return

        # Номера крайних линий по горизонтали.
        first_column = int(-origin_x // step) - 1
        last_column = int(
            (self.width() - origin_x) // step
        ) + 1

        # Номера крайних линий по вертикали.
        first_row = int(-origin_y // step) - 1
        last_row = int(
            (self.height() - origin_y) // step
        ) + 1

        # Вертикальные линии сетки.
        for i in range(first_column, last_column + 1):
            x = origin_x + i * step

            color = (
                self.major_grid_color
                if i % 5 == 0
                else self.grid_color
            )

            painter.setPen(QPen(QColor(color), 1))

            painter.drawLine(
                round(x), 0,
                round(x), self.height()
            )

        # Горизонтальные линии сетки.
        for i in range(first_row, last_row + 1):
            y = origin_y + i * step

            color = (
                self.major_grid_color
                if i % 5 == 0
                else self.grid_color
            )

            painter.setPen(QPen(QColor(color), 1))

            painter.drawLine(
                0, round(y),
                self.width(), round(y)
            )

    def draw_axes(self, painter, origin_x, origin_y):
        """Рисует оси X и Y и начало координат."""

        painter.setPen(
            QPen(QColor(self.axis_color), 2)
        )

        # Ось X.
        painter.drawLine(
            0, round(origin_y),
            self.width(), round(origin_y)
        )

        # Ось Y.
        painter.drawLine(
            round(origin_x), 0,
            round(origin_x), self.height()
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


    def world_to_screen(self, point):
        """Преобразует координаты чертежа в экранные."""
        scale = self.pixels_per_unit * self.zoom
        #self.origin_x экранная координата
        #point.x * scale смещение оси в пикселях
        x = self.origin_x + point.x * scale
        y = self.origin_y - point.y * scale

        return x, y


    def screen_to_world(self, x, y):
        """Преобразует экранные координаты в координаты чертежа."""
        scale = self.pixels_per_unit * self.zoom #вычисляем масштаб
        #x — координата курсора на экране в пикселях
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
        x2 = self.mouse_position.x()
        y2 = self.mouse_position.y()

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

        # Средняя кнопка мыши перемещает рабочую область.
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.last_mouse_pos = event.position()

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
        """Обрабатывает движение мыши."""

        # Перемещение рабочей области средней кнопкой.
        if (
            self.is_panning
            and self.last_mouse_pos is not None
        ):
            delta = event.position() - self.last_mouse_pos

            self.origin_x += delta.x()
            self.origin_y += delta.y()

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

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Завершает перемещение рабочей области."""

        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.last_mouse_pos = None

            if self.current_tool == "segment":
                self.setCursor(
                    Qt.CursorShape.CrossCursor
                )
            else:
                self.setCursor(
                    Qt.CursorShape.ArrowCursor
                )

            event.accept()
            return

        super().mouseReleaseEvent(event)

    def delete_segment_at(self, mouse_x, mouse_y):
        """Удаляет ближайший к курсору отрезок."""

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

    def wheelEvent(self, event):
        """Изменяет масштаб колёсиком мыши."""

        if self.origin_x is None or self.origin_y is None:
            self.origin_x = self.width() / 2
            self.origin_y = self.height() / 2

        # Положение курсора.
        mouse_x = event.position().x()
        mouse_y = event.position().y()

        # Направление изменения масштаба.
        if event.angleDelta().y() > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15

        # Ограничиваем масштаб.
        new_zoom = max(
            0.2,
            min(5.0, self.zoom * factor)
        )

        if new_zoom == self.zoom:
            event.accept()
            return

        actual_factor = new_zoom / self.zoom

        # Сохраняем положение точки под курсором.
        self.origin_x = (
            mouse_x
            - (mouse_x - self.origin_x) * actual_factor
        )

        self.origin_y = (
            mouse_y
            - (mouse_y - self.origin_y) * actual_factor
        )

        self.zoom = new_zoom
        self.update()
        event.accept()
