from dataclasses import dataclass
from math import pi, cos, sin
from typing import Self, NamedTuple

from plotly.graph_objs import Scatter


class Point(NamedTuple):
    x: float
    y: float


type VertexList = list[Point]

@dataclass
class Polygon:
    vertices: VertexList
    label: str = None
    color: str = None

    def __iter__(self):
        return iter(self.vertices)

    def to_scatter(self):
        vertices = self.vertices
        # Closing the polygon:
        vertices.append(vertices[0])

        x_coords, y_coords = zip(*vertices)
        return Scatter(
            x=x_coords, y=y_coords,
            mode='lines',
            fill='toself',
            fillcolor=self.color,
            opacity=1,
            line=dict(width=1, color='black'),
            showlegend=False,
            name=self.label,
        )


@dataclass
class Disc:
    center: Point
    radius: float

    @classmethod
    def from_circumference_points(cls, p1: Point, p2: Point, p3: Point) -> Self:
        ax, ay = p1.x, p1.y
        bx, by = p2.x, p2.y
        cx, cy = p3.x, p3.y

        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if d == 0:
            raise ValueError("The three points are collinear "
                             "— no unique circle exists.")
        ux = (
                     (ax ** 2 + ay ** 2) * (by - cy)
                     + (bx ** 2 + by ** 2) * (cy - ay)
                     + (cx ** 2 + cy ** 2) * (ay - by)
             ) / d
        uy = (
                     (ax ** 2 + ay ** 2) * (cx - bx)
                     + (bx ** 2 + by ** 2) * (ax - cx)
                     + (cx ** 2 + cy ** 2) * (bx - ax)
             ) / d

        radius = ((ax - ux) ** 2 + (ay - uy) ** 2) ** 0.5
        return cls(Point(ux, uy), radius)

    def to_vertices(self, edge_count=128) -> VertexList:
        # Let's do an approximation of the disc by making a 128 edge polygon:
        clockwise_vertices: list[Point] = []
        for i in reversed(range(edge_count)):
            angle = 2 * pi * i / edge_count
            x = self.center.x + self.radius * cos(angle)
            y = self.center.y + self.radius * sin(angle)
            clockwise_vertices.append(Point(x, y))
        return clockwise_vertices


def points_are_collinear(p1: Point, p2: Point, p3: Point) -> bool:
    x1, y1 = p2.x - p1.x, p2.y - p1.y
    x2, y2 = p3.x - p1.x, p3.y - p1.y
    return abs(x1 * y2 - x2 * y1) == 0


def get_constrained_size(img_w: int, img_h: int, max_w: int, max_h: int)\
        -> tuple[int, int]:
    ratio = img_w / img_h

    width_constrained_w = min(img_w, max_w)
    width_constrained_h = width_constrained_w / ratio

    height_and_width_constrained_h = min(width_constrained_h, max_h)
    height_and_width_constrained_w = height_and_width_constrained_h * ratio

    constrained_w = height_and_width_constrained_w
    constrained_h = height_and_width_constrained_h

    return round(constrained_w), round(constrained_h)
