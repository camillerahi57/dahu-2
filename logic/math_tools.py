from dataclasses import dataclass
from math import pi, cos, sin
from typing import Self, NamedTuple
import plotly.graph_objects as go

from plotly.graph_objs import Figure, Scatter


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

    def to_vertices(self, edge_nb=128) -> VertexList:
        # Let's do an approximation of the disc by making a 128 edge polygon:
        clockwise_vertices: list[Point] = []
        for i in reversed(range(edge_nb)):
            angle = 2 * pi * i / edge_nb
            x = self.center.x + self.radius * cos(angle)
            y = self.center.y + self.radius * sin(angle)
            clockwise_vertices.append(Point(x, y))
        return clockwise_vertices


def points_are_collinear(p1: Point, p2: Point, p3: Point) -> bool:
    x1, y1 = p2.x - p1.x, p2.y - p1.y
    x2, y2 = p3.x - p1.x, p3.y - p1.y
    return abs(x1 * y2 - x2 * y1) == 0