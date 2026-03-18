from abc import abstractmethod
from datetime import datetime
from random import Random

import chemparse
import numpy as np
from chemparse import parse_formula
from peewee import PostgresqlDatabase, Model, CharField, DateTimeField, ForeignKeyField, FloatField, IntegerField
from plotly.graph_objs import Scatter
# from peewee import *
from pyparsing import alphanums

from logic.constants import ChemicalElement, ShapeType
from logic.functions import letter_count

# FIELD TYPES:
# https://docs.peewee-orm.com/en/latest/peewee/models.html#fields

db = PostgresqlDatabase(
    'dahu2', user='postgres', password='postgres', host='localhost', port=5432
)


# Be careful, if an attribute is a foreignkey, you have to add '_id' at the end of the
# name of the column, in the
# DB table. This is because in the table, the key is actually store as an ID.
# The Model.create method is overridden to have argument autocompletion.


class BaseModel(Model):
    @classmethod
    @abstractmethod
    def new(cls, *args, **kwargs):
        """This just creates an instance of the object and returns it.
        So instead of doing: obj = Class()
        We do: obj = Class.new()
        It's useless, but it allows us to have PyCharm/VSCode warnings on have the correct
        arguments."""
        raise NotImplementedError  # Implement it in every subclass.

    class Meta:
        database = db
        legacy_table_names = False


class Experimenter(BaseModel):
    full_name = CharField()
    email_address = CharField()

    @classmethod
    def new(cls, full_name: str, email_address: str):
        return cls(full_name=full_name, email_address=email_address)


class Library(BaseModel):
    name = CharField()
    comment = CharField()
    made_at = DateTimeField()

    @classmethod
    def new(cls, name: str, comment: str, made_at: datetime):
        return cls(name=name, comment=comment, made_at=made_at)


class Characterization(BaseModel):
    name = CharField()
    experimenter = ForeignKeyField(Experimenter, on_delete='CASCADE')
    library = ForeignKeyField(Library, on_delete='CASCADE')

    @classmethod
    def new(cls, name: str, experimenter: Experimenter, library: Library):
        return cls(name=name, experimenter=experimenter, library=library)


class Stoichiometry(BaseModel):
    @classmethod
    def new(cls):
        return cls()

    def __str__(self):
        str_ = ''
        for e in self.elements:  # noqa for PyCharm.
            str_ += e.chemical_element_short
            if e.ratio_num != 1:
                str_ += f'{e.ratio_num:g}'
        return str_

    @classmethod
    def from_str(cls, formula: str) -> Stoichiometry:
        assert cls.is_valid_stoichio(formula)
        stoichio = cls.create()
        for short_element, quantity in parse_formula(formula).items():
            StoichiometryElement.create(
                chemical_element_short=short_element, ratio_num=quantity, stoichio=stoichio
            )
        return stoichio

    @staticmethod
    def is_valid_stoichio(stoichio_str: str) -> tuple[bool, str]:
        for char in stoichio_str:
            if char not in alphanums + '.':
                return False, f"Character '{char}' not allowed."
        stoichio_dict = chemparse.parse_formula(stoichio_str)
        for element in stoichio_dict.keys():
            if element not in ChemicalElement.all_short_str():
                return False, f"Unknown chemical element '{element}'."
        if letter_count(str(stoichio_dict)) != letter_count(stoichio_str):
            return False, f"Invalid syntax."
        if letter_count(str(stoichio_str)) == 0:
            return False, f"Requires at least one chemical element."
        return True, ''

    def rgb_color(self) -> tuple[int, int, int]:
        rng = Random(str(self))
        r = rng.randrange(0, 255)
        g = rng.randrange(0, 255)
        b = rng.randrange(0, 255)
        return r, g, b

    def plotly_color(self):
        r, g, b = self.rgb_color()
        return f'rgba({r},{g},{b},1)'

    def colored_rectangle_html(self):
        r, g, b = self.rgb_color()
        return f'<span style="color:rgb({r},{g},{b})">▮</span>'



class StoichiometryElement(BaseModel):
    chemical_element_short = CharField()
    ratio_num: float = FloatField()
    stoichio = ForeignKeyField(Stoichiometry, on_delete='CASCADE', backref='elements')

    @classmethod
    def new(cls, chemical_element_short: str, ratio_num: float, stoichio: Stoichiometry):
        return cls(chemical_element_short=chemical_element_short,
                   ratio_num=ratio_num, stoichio=stoichio)

    def __str__(self):
        return f'{self.chemical_element_short}{self.ratio_num}'


class Disc(BaseModel):
    center_x = FloatField()
    center_y = FloatField()
    radius = FloatField()

    @classmethod
    def new(cls, center_x: float, center_y: float, radius: float):
        return cls(center_x=center_x, center_y=center_y, radius=radius)

    def __str__(self):
        return (f"Center: ({self.center_x:g}, {self.center_y:g})"
                f"  |  Radius: {self.radius:g}")

    def to_scatter(self, color: str, name: str):
        cx, cy, r = self.center_x, self.center_y, self.radius

        # Parametric circle as a closed Scatter trace
        theta = np.linspace(0, 2 * np.pi, 360)
        x = cx + r * np.cos(theta)
        y = cy + r * np.sin(theta)

        return Scatter(
            x=x,
            y=y,
            mode='lines',
            fill='toself',
            fillcolor=color,
            opacity=1,
            line=dict(width=2, color='black'),
            showlegend=False,
            name=name
        )


class Polygon(BaseModel):
    @classmethod
    def new(cls):
        return cls()

    vertices: list[Vertex]  # backref of a foreign key in Vertex (see Vertex).

    def __str__(self):
        str_ = 'Vertices:'
        for v in self.ordered_vertices():
            str_ += f' {v}'
        return str_

    def ordered_vertices(self) -> list[Vertex]:
        return sorted(self.vertices, key=lambda x: x.clockwise_rank)

    def to_scatter(self, color: str, name: str) -> Scatter:
        vertex_list: list[tuple[float, float]] = [
            (v.x_pos, v.y_pos)
            for v in self.ordered_vertices()
        ]
        if vertex_list[-1] != vertex_list[0]:
            vertex_list.append(vertex_list[0])  # Close de loop.
        x_list, y_list = zip(*vertex_list)
        return Scatter(
            x=x_list, y=y_list,
            mode='lines',
            fill='toself',
            fillcolor=color,
            opacity=1,
            line=dict(width=2, color='black'),
            showlegend=False,
            name=name,
        )

    # @classmethod
    # def from_text(cls, text: str) -> tuple[Polygon|None, str]:
    #     """
    #     The input must be a list of vertices, one on each line. Each vertex is an X,Y couple.
    #     Example of a triangle:
    #     12.3, 48.3
    #     78, 15.6
    #     6.1, 5
    #     """
    #     allowed_non_blank_symbols = '.,-'
    #     digits = '0123456789'
    #     allowed_blanks = ' \n'
    #
    #     allowed_non_blank = digits + allowed_non_blank_symbols
    #     allowed_chars = allowed_non_blank_symbols + digits + allowed_blanks
    #
    #     for char in text:
    #         if char not in allowed_chars:
    #             msg = (f'Invalid character in polygons input. '
    #                    f'Allowed characters are: {allowed_non_blank}')
    #             return None, msg
    #     text = (text
    #             .replace(' ', '')  # Removes all white spaces.
    #             .strip(',\n')  # Allow dots at the start or end.
    #             )
    #     vertex_lines = filter(None, text.split('\n'))  # Removes empty as well.
    #     vertex_tuples: list[tuple[float, float]] = []
    #     for vertex_line in vertex_lines:
    #         try:
    #             x, y = vertex_line.removesuffix(',').split(',')
    #         except ValueError:
    #             msg = (f'All vertices must have 2 elements, '
    #                    f'got {len(vertex_line.split(','))}.')
    #             return None, msg
    #         vertex_tuples.append((float(x), float(y)))
    #     polygon = Polygon.from_ordered_vertices(vertex_tuples)
    #     return polygon, 'Success.'

# TODO Handle the replacement of create to new.

    @classmethod
    def from_ordered_vertices(cls, ordered_vertices: list[tuple[float, float]]) -> tuple[Polygon, list[Vertex]]:
        polygon = cls.new()
        vertices = []
        for i, (x, y) in enumerate(ordered_vertices):
            vertices.append(Vertex.new(x_pos=x, y_pos=y, clockwise_rank=i, polygon=polygon))
        return polygon, vertices


    @classmethod
    def from_aligned_rectangle_data(cls, first_vertex: tuple[float, float],
                                    opposite_vertex: tuple[float, float]) -> tuple[Polygon, list[Vertex]]:
        return Polygon.from_ordered_vertices(
            [
                (first_vertex[0], first_vertex[1]),
                (first_vertex[0], opposite_vertex[1]),
                (opposite_vertex[0], opposite_vertex[1]),
                (opposite_vertex[0], first_vertex[1]),
            ]
        )


class Vertex(BaseModel):
    x_pos: float = FloatField()
    y_pos: float = FloatField()
    clockwise_rank = IntegerField()
    polygon = ForeignKeyField(Polygon, on_delete='CASCADE', backref='vertices')

    @classmethod
    def new(cls, x_pos: float, y_pos: float, clockwise_rank: int, polygon: Polygon):
        return cls(x_pos=x_pos, y_pos=y_pos, clockwise_rank=clockwise_rank,
                              polygon=polygon)

    def __str__(self):
        return f'({self.x_pos:g}, {self.y_pos:g})'


class Shape(BaseModel):
    shape_type: ShapeType = CharField()
    polygon = ForeignKeyField(Polygon, on_delete='CASCADE', null=True)
    disc = ForeignKeyField(Disc, on_delete='CASCADE', null=True)

    @classmethod
    def new(cls, shape_type: ShapeType,
               polygon: Polygon=None, disc: Disc=None):
        return cls(shape_type=shape_type, polygon=polygon, disc=disc)

    def __str__(self):
        return str(self.polygon) if self.shape_type == ShapeType.POLYGON else str(self.disc)

    @classmethod
    def new_disc(cls, x_y_radius: tuple[float, float, float]) -> Shape:
        x, y, radius = x_y_radius
        disc = Disc.create(center_x=x, center_y=y, radius=radius)
        return cls.create(shape_type=ShapeType.DISC, disc=disc)

    @classmethod
    def new_polygon(cls, clockwise_vertices: list[tuple[float, float]]) -> Shape:
        polygon = Polygon.create()
        for i, (x, y) in enumerate(clockwise_vertices):
            Vertex.create(x_pos=x, y_pos=y, clockwise_rank=i, polygon=polygon)
        return cls.create(shape_type=ShapeType.POLYGON, polygon=polygon)


class Patch(BaseModel):
    stoichiometry = ForeignKeyField(Stoichiometry, on_delete='CASCADE')
    shape = ForeignKeyField(Shape, on_delete='CASCADE')
    # TODO Add target attribute here.

    @classmethod
    def new(cls, shape: Shape, stoichiometry: Stoichiometry):
        return cls(shape=shape, stoichiometry=stoichiometry)

    def __str__(self):
        return f'Patch: {self.stoichiometry} of shape:\n{self.shape})'

    @classmethod
    def new_disc(cls, stoichio: str, x_y_radius: tuple[float, float, float]) -> Patch:
        shape = Shape.new_disc(x_y_radius=x_y_radius)
        stoichio = Stoichiometry.from_str(stoichio)
        patch = cls.create(stoichiometry=stoichio, shape=shape)
        return patch

    @classmethod
    def new_polygon(cls, stoichio: str,
                    clockwise_vertices: list[tuple[float, float]]) -> Patch:
        stoichio = Stoichiometry.from_str(stoichio)
        shape = Shape.new_polygon(clockwise_vertices=clockwise_vertices)
        return cls.create(stoichiometry=stoichio, shape=shape)


class Target(BaseModel):
    made_at = DateTimeField()
    made_by_email: str = CharField()
    target_name: str = CharField()
    comment: str = CharField()

    @classmethod
    def new(cls, made_at: datetime, made_by_email: str, target_name: str, comment: str):
        return cls(made_at=made_at, made_by_email=made_by_email, target_name=target_name,
                   comment=comment)

    @classmethod
    def already_taken_names(cls):
        # TODO
        return []