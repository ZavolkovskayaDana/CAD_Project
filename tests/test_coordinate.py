
from geometry.coordinates import (
    polar_to_cartesian,
    cartesian_to_polar,
)

# Преобразуем полярные координаты в декартовы.
x, y = polar_to_cartesian(5, 53.13010235415598)

print("Декартовы координаты:", x, y)

# Преобразуем полученные координаты обратно.
r, theta = cartesian_to_polar(x, y)

print("Полярные координаты:", r, theta)

# Проверяем работу с радианами.
x_rad, y_rad = polar_to_cartesian(
    5,
    0.9272952180016122,
    degrees=False,
)

print("Результат с углом в радианах:", x_rad, y_rad)
