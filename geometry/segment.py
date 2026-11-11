
import math

from geometry.point import Point


class Segment:
    """Представляет отрезок между двумя точками."""

    def __init__(
        self,
        start,
        end,
        input_angle=None,
        input_angle_degrees=None,
    ):
        if not isinstance(start, Point):
            raise TypeError("Начало отрезка должно быть объектом Point")

        if not isinstance(end, Point):
            raise TypeError("Конец отрезка должен быть объектом Point")

        self.start = start
        self.end = end

        # Исходный угол, введённый пользователем.
        # None означает, что отрезок задан не полярным углом.
        self.input_angle = input_angle
        self.input_angle_degrees = input_angle_degrees

    @property
    def length(self):
        """Возвращает длину отрезка."""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y

        return math.hypot(dx, dy)

    @property
    def angle(self):
        """
        Возвращает геометрический угол направления отрезка
        в радианах в диапазоне [-pi, pi].
        """
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y

        return math.atan2(dy, dx)

    def __repr__(self):
        return (
            f"Segment(start={self.start}, end={self.end}, "
            f"input_angle={self.input_angle}, "
            f"input_angle_degrees={self.input_angle_degrees})"
        )
