from math import sqrt


def add_points(p1, p2, inverse=False):
    """
    Returns the sum of two coordinate pairs, or the difference of
    the first and second point passed.

    :param p1: tuple (int or float, int or float)
    :param p2: tuple (int or float, int or float)
    :param inverse: bool, optional flag to subtract p2 from p1
        and return the difference

    :return: tuple (int or float, int or float)
    """
    x1, y1 = p1
    x2, y2 = p2

    if inverse:
        x2 *= -1
        y2 *= -1

    return x1 + x2, y1 + y2


def get_distance(p1, p2):
    """
    Returns the Euclidean distance value between two coordinate pairs

    :param p1: tuple (int or float, int or float)
    :param p2: tuple (int or float, int or float)

    :return: float, distance value
    """
    x1, y1 = p1
    x2, y2 = p2

    dx = abs(x1 - x2)
    dy = abs(y1 - y2)

    return sqrt(dx**2 + dy**2)
