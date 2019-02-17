from math import sqrt


def add_points(p1, p2, inverse=False):
    x1, y1 = p1
    x2, y2 = p2

    if inverse:
        x2 *= -1
        y2 *= -1

    return x1 + x2, y1 + y2


def get_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dx = abs(x1 - x2)
    dy = abs(y1 - y2)

    return sqrt(dx**2 + dy**2)
