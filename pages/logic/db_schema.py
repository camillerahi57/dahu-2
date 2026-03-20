from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from random import Random
from uuid import uuid4

import chemparse
from peewee import PostgresqlDatabase, Model, CharField, DateTimeField, ForeignKeyField, FloatField, IntegerField, \
    UUIDField
from plotly.graph_objs import Scatter
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
    id = UUIDField(primary_key=True, default=uuid4)

    @classmethod
    @abstractmethod  # noqa
    def new(cls, *args, **kwargs):
        """This just creates an instance of the object and returns it.
        So instead of doing: obj = Class()
        We do: obj = Class.new()
        It's useless, but it allows us to have PyCharm/VSCode warnings on have the correct
        arguments."""
        raise NotImplementedError  # Implement it in every subclass.

    def save(self, *args, **kwargs):
        """As written on top of this, we use UUID4 instead of the default Peewee ID. This allows
        us to instantiate a model with an id already set.

        However, this creates a bug where Peewee .save() method is always updating, instead of saving a new
        object in the database. That's why we have to override this .save() method and add 'force_insert'
        in case get_or_none returns None (which means it's a new row, in which case it's an insert."""
        if not kwargs.get('force_insert') and not self.__class__.get_or_none(self.__class__.id == self.id):
            kwargs['force_insert'] = True
        return super().save(*args, **kwargs)

    class Meta:
        database = db
        legacy_table_names = False


# class Experimenter(BaseModel):
#     full_name = CharField()
#     email_address = CharField()
#
#     @classmethod
#     def new(cls, full_name: str, email_address: str):
#         return cls(full_name=full_name, email_address=email_address)
#
#
# class Library(BaseModel):
#     name = CharField()
#     comment = CharField()
#     made_at = DateTimeField()
#
#     @classmethod
#     def new(cls, name: str, comment: str, made_at: datetime):
#         return cls(name=name, comment=comment, made_at=made_at)
#
#
# class Characterization(BaseModel):
#     name = CharField()
#     experimenter = ForeignKeyField(Experimenter, on_delete='CASCADE')
#     library = ForeignKeyField(Library, on_delete='CASCADE')
#
#     @classmethod
#     def new(cls, name: str, experimenter: Experimenter, library: Library):
#         return cls(name=name, experimenter=experimenter, library=library)


class Target(BaseModel):
    made_at = DateTimeField()
    made_by_email = CharField()
    target_name = CharField(unique=True)
    comment = CharField()
    photo_path = CharField(unique=True)

    @classmethod
    def new(cls, made_at: datetime, made_by_email: str, target_name: str, comment: str, photo_path: str|Path):
        return cls(made_at=made_at, made_by_email=made_by_email, target_name=target_name,
                   comment=comment, photo_path=photo_path)

    @classmethod
    def already_taken_names(cls):
        query = Target.select(
            Target.target_name
        ).dicts()
        names = [row[Target.target_name.name]
                 for row in query]
        return names


class Patch(BaseModel):
    rank_from_back_to_front = IntegerField()
    stoichio = CharField()
    shape_type: ShapeType = CharField()  # Do we have to keep it?
    target = ForeignKeyField(Target, on_delete='CASCADE')

    @classmethod
    def new(cls, rank_from_back_to_front: int, stoichio: str, target: Target, shape_type: ShapeType):
        return cls(rank_from_back_to_front=rank_from_back_to_front, stoichio=stoichio, target=target,
                   shape_type=shape_type)

    def __str__(self):
        return f'Patch of stoichiometry {self.stoichio}'

    @classmethod
    def new_disc_patch(cls, stoichio: str, x_y_radius: tuple[float, float, float], target: Target,
                       rank_from_back_to_front: int) \
            -> tuple[Patch, Disc]:
        x, y, radius = x_y_radius
        patch = cls.new(rank_from_back_to_front, stoichio, target, ShapeType.DISC)
        disc = Disc.new(center_x=x, center_y=y, radius=radius, patch=patch)
        return patch, disc

    @classmethod
    def new_polygon_patch(cls, stoichio: str, clockwise_vertices: list[tuple[float, float]],
                          rank_from_back_to_front: int, target: Target) \
            -> tuple[Patch, Polygon, list[Vertex]]:
        patch = cls.new(rank_from_back_to_front, stoichio, target, ShapeType.POLYGON)
        polygon, vertices = Polygon.from_ordered_vertices(
            clockwise_vertices=clockwise_vertices, patch=patch
        )
        return patch, polygon, vertices

    @staticmethod
    def is_valid_stoichio(stoichio_str: str) -> tuple[bool, str]:
        for char in stoichio_str:
            if char not in alphanums + '.':
                return False, f"Character '{char}' not allowed."
        stoichio_dict = chemparse.parse_formula(stoichio_str)
        for element in stoichio_dict:
            if element not in ChemicalElement.all_short_str():
                return False, f"Unknown chemical element '{element}'."
        if letter_count(str(stoichio_dict)) != letter_count(stoichio_str):
            return False, f"Invalid syntax."
        if letter_count(str(stoichio_str)) == 0:
            return False, f"Requires at least one chemical element."
        return True, ''

    @staticmethod
    def rgb_color(stoichio_str: str) -> tuple[int, int, int]:
        rng = Random(stoichio_str)
        r = rng.randrange(0, 255)
        g = rng.randrange(0, 255)
        b = rng.randrange(0, 255)
        return r, g, b

    @staticmethod
    def plotly_color(stoichio_str: str):
        r, g, b = Patch.rgb_color(stoichio_str)
        return f'rgba({r},{g},{b},1)'

    @staticmethod
    def colored_rectangle_html(stoichio_str: str):
        r, g, b = Patch.rgb_color(stoichio_str)
        return f'<span style="color:rgb({r},{g},{b})">▮</span>'


class Disc(BaseModel):
    center_x = FloatField()
    center_y = FloatField()
    radius = FloatField()
    patch = ForeignKeyField(Patch, on_delete='CASCADE', unique=True)

    @classmethod
    def new(cls, center_x: float, center_y: float, radius: float, patch: Patch):
        return cls(center_x=center_x, center_y=center_y, radius=radius, patch=patch)

    def __str__(self):
        return (f"Center: ({self.center_x:g}, {self.center_y:g})"
                f"  |  Radius: {self.radius:g}")


class Polygon(BaseModel):
    patch = ForeignKeyField(Patch, on_delete='CASCADE', unique=True)

    @classmethod
    def new(cls, patch: Patch):
        return cls(patch=patch)

    vertices: list[Vertex]  # backref of a foreign key in Vertex (see Vertex).

    def __str__(self):
        str_ = 'Vertices:'
        for v in self.saved_ordered_vertices():
            str_ += f' {v}'
        return str_

    def saved_ordered_vertices(self) -> list[Vertex]:
        return sorted(self.vertices, key=lambda x: x.clockwise_rank)

    def to_scatter(self, color: str, name: str) -> Scatter:
        vertex_list: list[tuple[float, float]] = [
            (v.x_pos, v.y_pos)
            for v in self.saved_ordered_vertices()
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
    #      )
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


    @classmethod
    def from_ordered_vertices(cls, clockwise_vertices: list[tuple[float, float]], patch: Patch) \
            -> tuple[Polygon, list[Vertex]]:
        polygon = cls.new(patch=patch)
        vertices = []
        for i, (x, y) in enumerate(clockwise_vertices):
            vertices.append(Vertex.new(x_pos=x, y_pos=y, clockwise_rank=i, polygon=polygon))
        return polygon, vertices


    @classmethod
    def from_aligned_rectangle_data(cls, first_vertex: tuple[float, float],
                                    opposite_vertex: tuple[float, float], patch: Patch) \
            -> tuple[Polygon, list[Vertex]]:
        return Polygon.from_ordered_vertices(
            [
                (first_vertex[0], first_vertex[1]),
                (first_vertex[0], opposite_vertex[1]),
                (opposite_vertex[0], opposite_vertex[1]),
                (opposite_vertex[0], first_vertex[1]),
            ],
            patch=patch,
        )


class Vertex(BaseModel):
    x_pos: float = FloatField()
    y_pos: float = FloatField()
    clockwise_rank = IntegerField()
    polygon = ForeignKeyField(Polygon, on_delete='CASCADE', backref='vertices')

    @classmethod
    def new(cls, x_pos: float, y_pos: float, clockwise_rank: int, polygon: Polygon) -> Vertex:
        return cls(x_pos=x_pos, y_pos=y_pos, clockwise_rank=clockwise_rank,
                              polygon=polygon)

    def __str__(self):
        return f'({self.x_pos:g}, {self.y_pos:g})'
