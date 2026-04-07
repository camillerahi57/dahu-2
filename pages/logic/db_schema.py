from abc import abstractmethod
from datetime import datetime
from random import Random
from typing import Self
from uuid import uuid4

import plotly.graph_objects as go
import chemparse
from peewee import PostgresqlDatabase, Model, CharField, DateTimeField, ForeignKeyField, FloatField, IntegerField, \
    UUIDField, BooleanField
from plotly.graph_objs import Scatter
from pyparsing import alphanums
from streamlit.runtime.uploaded_file_manager import UploadedFile

from logic.constants import ChemicalElement, FILE_STORAGE_PATH
from logic.db_enums import ShapeType, SputteringSystem, FilmLayerFunction, MagnetronSputteringGenerator
from logic.functions import letter_count, disc_patch_to_scatter, polygon_patch_to_scatter

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

        However, this creates a bug where Peewee .save() method is always updating, instead
        of saving a new object in the database. That's why we have to override this .save()
        method and add 'force_insert' in case get_or_none returns None (which means it's a
        new row, in which case it's an insert."""
        if (not kwargs.get('force_insert')
                and not self.__class__.get_or_none(self.__class__.id == self.id)):
            kwargs['force_insert'] = True
        return super().save(*args, **kwargs)

    class Meta:
        database = db
        legacy_table_names = False

class Target(BaseModel):
    made_at = DateTimeField()
    made_by_email = CharField()
    physical_name = CharField(unique=True)
    comment = CharField()
    photo_file_name = CharField(unique=True)

    @classmethod
    def new(cls, made_at: datetime, made_by_email: str, physical_name: str, comment: str,
            photo_file_name: str):
        return cls(made_at=made_at, made_by_email=made_by_email, physical_name=physical_name,
                   comment=comment, photo_file_name=photo_file_name)

    @classmethod
    def already_taken_names(cls):
        query = Target.select(
            Target.physical_name
        ).dicts()
        names = [row[Target.physical_name.name]
                 for row in query]
        return names

    def to_plotly_figure(self):
        fig = go.Figure(
            [Scatter()],
            layout=go.Layout(xaxis={'showgrid': True}, yaxis={'scaleanchor': 'x'}),
        )
        patches = Patch.select().where(Patch.target == self.id)
        for patch in patches:
            fig.add_trace(patch.to_scatter())
        return fig

    @classmethod
    def from_name(cls, name: str) -> Self:
        return Target.get(Target.physical_name == name)

    def photo_path(self):
        return FILE_STORAGE_PATH / self.photo_file_name


class Patch(BaseModel):
    rank_from_back_to_front = IntegerField()
    stoichio = CharField()
    shape_type: ShapeType = CharField()
    is_target_base = BooleanField()
    target = ForeignKeyField(Target, on_delete='CASCADE')

    @classmethod
    def new(cls, rank_from_back_to_front: int, stoichio: str, target: Target,
            shape_type: ShapeType, is_target_base: bool):
        return cls(rank_from_back_to_front=rank_from_back_to_front, stoichio=stoichio,
                   target=target, shape_type=shape_type, is_target_base=is_target_base)

    def __str__(self):
        return f'Patch of stoichiometry {self.stoichio}'

    @classmethod
    def new_disc_patch(cls, stoichio: str, x_y_radius: tuple[float, float, float], target: Target,
                       rank_from_back_to_front: int, is_target_base: bool) \
            -> tuple[Patch, Disc]:
        x, y, radius = x_y_radius
        patch = cls.new(rank_from_back_to_front, stoichio, target, ShapeType.DISC, is_target_base)
        disc = Disc.new(center_x=x, center_y=y, radius=radius, patch=patch)
        return patch, disc

    @classmethod
    def new_polygon_patch(cls, stoichio: str, clockwise_vertices: list[tuple[float, float]],
                          rank_from_back_to_front: int, target: Target, is_target_base: bool) \
            -> tuple[Patch, Polygon, list[Vertex]]:
        patch = cls.new(rank_from_back_to_front, stoichio, target, ShapeType.POLYGON,
                        is_target_base)
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

    def to_scatter(self):
        # user = User.select().where(User.username == 'charlie').get()
        color = self.plotly_color(str(self.stoichio))
        name = str(self.stoichio)
        if self.shape_type == ShapeType.DISC:
            disc = Disc.get(Disc.patch == self.id)
            return disc_patch_to_scatter(
                x_y_radius=(disc.center_x, disc.center_y, disc.radius),
                color_=color,
                name_=name,
            )
        elif self.shape_type == ShapeType.POLYGON:
            polygon = Polygon.get(Polygon.patch == self.id)
            vertices = polygon.saved_ordered_vertices()
            vertex_coords = [(v.x_pos, v.y_pos) for v in vertices]
            return polygon_patch_to_scatter(vertex_coords, color_=color, name_=name)
        else:
            raise ValueError(f"Unknown shape_type '{str(self.shape_type)}'.")



class Disc(BaseModel):
    center_x = FloatField()
    center_y = FloatField()
    radius = FloatField()
    patch = ForeignKeyField(Patch, on_delete='CASCADE')

    @classmethod
    def new(cls, center_x: float, center_y: float, radius: float, patch: Patch):
        return cls(center_x=center_x, center_y=center_y, radius=radius, patch=patch)

    def __str__(self):
        return (f"Center: ({self.center_x:g}, {self.center_y:g})"
                f"  |  Radius: {self.radius:g}")


class Polygon(BaseModel):
    patch = ForeignKeyField(Patch, on_delete='CASCADE')

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
            line=dict(width=1, color='black'),
            showlegend=False,
            name=name,
        )

    @classmethod
    def from_text(cls, text: str, patch: Patch) -> tuple[Polygon, list[Vertex]]:
        vertex_tuples = cls.polygon_text_to_vertices(text)
        polygon, vertices = Polygon.from_ordered_vertices(vertex_tuples, patch)
        return polygon, vertices

    @staticmethod
    def polygon_text_to_vertices(text: str) -> list[tuple[float, float]]:
        """
        The input must be a list of vertices, one on each line. Each vertex is an X,Y couple.
        Example of a triangle:
        12.3, 48.3
        78, 15.6
        6.1, 5
        """
        text = (text
                .replace(' ', '')  # Removes all white spaces.
                .strip(',\n')  # Allow dots at the start or end.
         )
        vertex_lines = filter(None, text.split('\n'))  # Removes empty as well.
        vertex_tuples: list[tuple[float, float]] = []
        for vertex_line in vertex_lines:
            x, y = vertex_line.removesuffix(',').split(',')
            vertex_tuples.append((float(x), float(y)))
        return vertex_tuples



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


class Substrate(BaseModel):
    name = CharField(unique=True)
    comment = CharField()

    @classmethod
    def new(cls, name: str, comment: str) -> Substrate:
        return cls(name=name, comment=comment)

    @classmethod
    def already_taken_names(cls):
        query = Substrate.select(
            Substrate.name
        ).dicts()
        names = [row[Substrate.name.name]  # Name of the name field (which is 'name'),
                 # not the name itself.
                 for row in query]
        return names


class SubstrateLayer(BaseModel):
    thickness = FloatField()
    h = IntegerField()
    k = IntegerField()
    l = IntegerField()
    stoichiometry = CharField()
    substrate = ForeignKeyField(Substrate, on_delete='CASCADE', backref='layers')

    @classmethod
    def new(cls, thickness: float, h: int, k: int, l: int, stoichiometry: str,
            substrate: Substrate)\
            -> SubstrateLayer:
        return cls(thickness=thickness, h=h, k=k, l=l, stoichiometry=stoichiometry,
                   substrate=substrate)


class MokeCoilFactor(BaseModel):
    validity_start = DateTimeField()
    validity_end = DateTimeField()
    factor = FloatField()

    @classmethod
    def new(cls, validity_start: datetime, validity_end: datetime, factor: float) \
            -> MokeCoilFactor:
        return cls(validity_start=validity_start, validity_end=validity_end, factor=factor)


class EsrfPoni(BaseModel):
    validity_start = DateTimeField()
    validity_end = DateTimeField()
    distance = FloatField()
    poni1 = FloatField()
    poni2 = FloatField()
    rot1 = FloatField()
    rot2 = FloatField()
    rot3 = FloatField()
    wavelength = FloatField()

    @classmethod
    def new(cls, validity_start: datetime, validity_end: datetime, distance: float, poni1: float,
            poni2: float, rot1: float, rot2: float, rot3: float, wavelength: float)\
            -> EsrfPoni:
        return cls(validity_start=validity_start, validity_end=validity_end, distance=distance,
                   poni1=poni1, poni2=poni2, rot1=rot1, rot2=rot2, rot3=rot3,
                   wavelength=wavelength)


class Film(BaseModel):
    physical_name = CharField(unique=True)
    made_at = DateTimeField()
    made_by_email = CharField()
    substrate = ForeignKeyField(Substrate)

    @classmethod
    def new(cls, physical_name: str, made_at: datetime, made_by_email: str, substrate: Substrate)\
            -> Film:
        return cls(physical_name=physical_name, made_at=made_at, made_by_email=made_by_email,
                   substrate=substrate)

    @classmethod
    def already_taken_names(cls):
        query = Film.select(
            Film.physical_name
        ).dicts()
        names = [row[Film.physical_name.name]
                 for row in query]
        return names


class Library(BaseModel):
    name = CharField(unique=True)
    last_inspected_at = DateTimeField()
    comment = CharField()
    film = ForeignKeyField(Film)
    # TODO HDF5 file name here.

    @classmethod
    def new(cls, name: str, last_inspected_at: datetime, comment: str, film: Film) -> Library:
        return cls(name=name, last_inspected_at=last_inspected_at, comment=comment, film=film)

    @classmethod
    def already_taken_names(cls):
        query = cls.select(
            cls.name
        ).dicts()
        names = [row[cls.name.name]
                 for row in query]
        return names


class FilmLayer(BaseModel):
    position_from_buffer = IntegerField()
    deposit_temp = FloatField()
    deposit_duration = FloatField()
    deposit_power = FloatField()
    thickness = FloatField()
    stoichiometry = CharField()
    function: FilmLayerFunction = CharField()
    sputtering_system: SputteringSystem = CharField()
    film = ForeignKeyField(Film, on_delete='CASCADE', backref='layers')
    target = ForeignKeyField(Target)

    @classmethod
    def new(cls, position_from_buffer: int, deposit_temp: float, deposit_duration: float,
            deposit_power: float, thickness: float, stoichiometry: str,
            function: FilmLayerFunction, film: Film, target: Target,
            sputtering_system: SputteringSystem) \
            -> FilmLayer:
        return cls(position_from_buffer=position_from_buffer, deposit_temp=deposit_temp,
                   deposit_duration=deposit_duration, deposit_power=deposit_power,
                   thickness=thickness, stoichiometry=stoichiometry, function=function, film=film,
                   target=target, sputtering_system=sputtering_system)


class MagnetronSputtering(BaseModel):
    deposit_distance = FloatField()
    deposit_angle = FloatField()
    generator: MagnetronSputteringGenerator = CharField()
    film_layer = ForeignKeyField(FilmLayer, on_delete='CASCADE')

    @classmethod
    def new(cls, deposit_distance: float, deposit_angle: float,
            generator: MagnetronSputteringGenerator, film_layer: FilmLayer) \
        -> MagnetronSputtering:
        return cls(deposit_distance=deposit_distance, deposit_angle=deposit_angle,
                   generator=generator, film_layer=film_layer)


class TriodeSputtering(BaseModel):  # TODO Add default values in front-end.
    has_active_cooling = BooleanField()
    rotation = FloatField()
    filament_tension = FloatField()
    film_layer = ForeignKeyField(FilmLayer, on_delete='CASCADE')

    @classmethod
    def new(cls, has_active_cooling: bool, rotation: float, filament_tension: float,
            film_layer: FilmLayer) -> TriodeSputtering:
        return cls(has_active_cooling=has_active_cooling, rotation=rotation,
                   filament_tension=filament_tension, film_layer=film_layer)


class UserUploadedFile(BaseModel):
    file_name = CharField(unique=True)

    @classmethod
    def new(cls, file_name: str) -> UserUploadedFile:
        return cls(file_name=file_name)

    @classmethod
    def from_streamlit_uploaded_file(cls, upload_field: UploadedFile) -> UserUploadedFile:
        extension = upload_field.name.split('.')[-1]
        file_name = f'{uuid4()}.{extension}'
        return cls.new(file_name=file_name)





# TODO DB integrity verification routine.