from geometry.point import Point
from geometry.segment import Segment


# Создаём две точки.
point_a = Point(0, 0)
point_b = Point(3, 4)

# Создаём отрезок между ними.
segment = Segment(point_a, point_b)

print("Точка A:", point_a)
print("Точка B:", point_b)
print("Отрезок:", segment)
print("Длина:", segment.length)
print("Угол в радианах:", segment.angle)
print("Угол в градусах:", segment.angle * 180 / 3.141592653589793)
