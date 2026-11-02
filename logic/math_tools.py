"""Small geometry and unit helpers: points, polygons, discs, image size
fitting and conversion of Pint quantities to plain numbers.

Points are 2D coordinates. For the target photos they are pixel
coordinates (see `PixelCoordinateSystem` in `db_enums`), not metres.
"""

from dataclasses import dataclass
from math import pi, cos, sin
from typing import Self, NamedTuple

from pint.registry import Quantity, Unit
from plotly.graph_objs import Scatter


class Point(NamedTuple):
    """A 2D point.

    A `NamedTuple` is a tuple whose items also have names, so `p.x` and
    `p[0]` are the same. Being a tuple, a `Point` is immutable and can be
    put in a set or compared with `==`.

    Attributes:
        x: First coordinate.
        y: Second coordinate.
    """
    x: float
    y: float


# A type alias (a new name for an existing type): the corners of a
# polygon, in drawing order.
type VertexList = list[Point]

@dataclass
class Polygon:
    """A polygon to draw with Plotly.

    A dataclass is a class whose `__init__` is written automatically from
    its annotated attributes. Iterating over a `Polygon` iterates over
    its vertices. No code in the repo uses this class at the moment (a
    `Patch` has its own `to_scatter`).

    Attributes:
        vertices: Corners, in drawing order. The polygon is closed
            automatically when drawn.
        label: Name shown on hover, or None.
        color: Fill colour as a CSS/Plotly colour string, or None.
    """
    vertices: VertexList
    label: str|None = None
    color: str|None = None

    def __iter__(self):
        """Iterates over the vertices."""
        return iter(self.vertices)

    def to_scatter(self):
        """Builds the Plotly trace that draws this polygon.

        Side effect: the first vertex is appended at the end of
        `self.vertices` (to close the outline), so calling this twice
        adds it twice.

        Returns:
            A filled `Scatter` trace with a thin black outline and no
            legend entry.
        """
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
    # TODO It appends the first vertex
    #   to `self.vertices` itself, so every call grows the list (and a polygon
    #   drawn twice gets a duplicated closing vertex). Work on a copy instead?


@dataclass
class Disc:
    """A disc, i.e. a filled circle, in the same 2D coordinates as
    `Point`.

    Attributes:
        center: Centre of the disc.
        radius: Radius, in the same unit as the point coordinates.
    """
    center: Point
    radius: float

    @classmethod
    def from_circumference_points(cls, p1: Point, p2: Point, p3: Point) -> Self:
        """Builds the disc whose circumference goes through three points.

        Uses the closed formula for the circle through three points (the
        circumcircle of the triangle they form).

        Args:
            p1: First point on the circumference.
            p2: Second point on the circumference.
            p3: Third point on the circumference.

        Returns:
            The disc.

        Raises:
            ValueError: If the points are aligned (the determinant
                is exactly 0), because no circle goes through them.
        """
        ax, ay = p1.x, p1.y
        bx, by = p2.x, p2.y
        cx, cy = p3.x, p3.y

        # d is 0 if and only if the three points are aligned.
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if d == 0:
            raise ValueError("The three points are collinear "
                             "— no unique circle exists.")
        # (ux, uy) is the centre of the circle.
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
        """Approximates the disc by a regular polygon.

        Patches are stored in the DB as polygons only, so a disc has to
        be converted before saving (see `Patch.from_polygon`).

        Args:
            edge_count: Number of edges (= number of vertices) of the
                polygon. More edges give a rounder disc.

        Returns:
            The vertices, starting at angle 0 and going round with the
            angle decreasing (clockwise if the y axis points up).
        """
        # Let's do an approximation of the disc by making a 128 edge polygon:
        clockwise_vertices: list[Point] = []
        for i in reversed(range(edge_count)):
            angle = 2 * pi * i / edge_count
            x = self.center.x + self.radius * cos(angle)
            y = self.center.y + self.radius * sin(angle)
            clockwise_vertices.append(Point(x, y))
        return clockwise_vertices


def points_are_collinear(p1: Point, p2: Point, p3: Point) -> bool:
    """Tells whether three points lie on one straight line.

    The test is exact (floating-point equality to 0), so points that are
    only almost aligned give False.

    Args:
        p1: First point.
        p2: Second point.
        p3: Third point.

    Returns:
        True if the cross product of the vectors p1->p2 and p1->p3 is
        exactly 0.
    """
    x1, y1 = p2.x - p1.x, p2.y - p1.y
    x2, y2 = p3.x - p1.x, p3.y - p1.y
    return abs(x1 * y2 - x2 * y1) == 0


def get_constrained_size(img_w: int, img_h: int, max_w: int, max_h: int)\
        -> tuple[int, int]:
    """Shrinks an image size to fit in a box, keeping its aspect ratio.

    A size that already fits is returned unchanged (images are never
    enlarged).

    Args:
        img_w: Image width, in pixels.
        img_h: Image height, in pixels.
        max_w: Maximum width, in pixels.
        max_h: Maximum height, in pixels.

    Returns:
        The new (width, height), in pixels, rounded to integers.
    """
    ratio = img_w / img_h

    width_constrained_w = min(img_w, max_w)
    width_constrained_h = width_constrained_w / ratio

    height_and_width_constrained_h = min(width_constrained_h, max_h)
    height_and_width_constrained_w = height_and_width_constrained_h * ratio

    constrained_w = height_and_width_constrained_w
    constrained_h = height_and_width_constrained_h

    return round(constrained_w), round(constrained_h)


def to_float(quantity: Quantity|None, unit: Unit) -> float|None:
    """Converts a Pint quantity to a plain number in the given unit.

    Args:
        quantity: The physical quantity (value with unit), or None.
        unit: The unit of the returned number.

    Returns:
        The magnitude of `quantity` expressed in `unit`, or None if
        `quantity` is None.
    """
    return quantity.to(unit).magnitude if quantity is not None else None
