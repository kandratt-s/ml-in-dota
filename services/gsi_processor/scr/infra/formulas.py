from math import hypot

from scr.infra.config import settings


def euclidean_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    return int(hypot(x1 - x2, y1 - y2))


def cell_id(x: int, y: int) -> int:
    """
    Считаем id ячейки на карте начиная от 0 в левом нижнем углу
    до 1023 в правом верхнем, при CELLS=32.
    """
    xmin, xmax, ymin, ymax, cells = (
        settings.XMIN,
        settings.XMAX,
        settings.YMIN,
        settings.YMAX,
        settings.CELLS,
    )

    return int((y - ymin) / (ymax - ymin) * cells) * cells + int((x - xmin) / (xmax - xmin) * cells)