
class Point:
    """Представляет точку на двумерной координатной плоскости."""

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return f"Point(x={self.x}, y={self.y})"
