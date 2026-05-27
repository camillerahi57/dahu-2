import inspect
import sys
from datetime import datetime
from pathlib import Path
from random import Random
from typing import Self, get_type_hints, Iterable, Any, final
from uuid import uuid4

import chemparse
import plotly.graph_objects as go
from peewee import PostgresqlDatabase, Model, CharField, DateTimeField, \
    ForeignKeyField, FloatField, IntegerField, \
    UUIDField, BooleanField, DateField
from playhouse.shortcuts import model_to_dict  # noqa
from plotly.graph_objs import Scatter
from pyparsing import alphanums
from streamlit.runtime.uploaded_file_manager import UploadedFile

from logic.constants import ChemicalElement, FILE_STORAGE_PATH, DOMAIN, \
    LIB_ID_URL_KEY, SUB_ID_URL_KEY, TARGET_ID_URL_KEY, PATTERN_IMAGE_PATH
from logic.db_enums import SputteringSystem, FilmLayerFunction, \
    MagnetronSputteringGenerator, FilmModifType, Furnace, \
    MagnetronMachineModel, PixelCoordinateSystem
from logic.functions import letter_count
from logic.math_tools import VertexList

# FIELD TYPES:
# https://docs.peewee-orm.com/en/latest/peewee/models.html#fields

db = PostgresqlDatabase(
    'dahu2', user='postgres', password='postgres', host='localhost', port=5432
)

# Be careful, if an attribute is a foreignkey, you have to add '_id' at the
# end of the name of the column, in the DB table. This is because in the
# table, the key is actually store as an ID. The Model.create method is
# overridden to have argument autocompletion.


type CascadingBackref[T] = list[T]
type Backref[T] = list[T]


class _BaseModel(Model):
    id = UUIDField(primary_key=True, default=uuid4)

    # @classmethod
    # def from_fields(cls, field_values: dict[Field, Any]):
    #     kwargs = {f.name: v for f, v in field_values.items()}
    #     return cls(**kwargs)

    def save(self, *args, **kwargs):
        """As written on top of this, we use UUID4 instead of the default
        Peewee ID. This allows us to instantiate a model with an id already set.

        However, this creates a bug where Peewee .save() method is always
        updating, instead of saving a new object in the database. That's why
        we have to override this .save() method and add 'force_insert' in
        case get_or_none returns None (which means it's a new row, in which
        case it's an insert)."""
        cls = self.__class__
        if (not kwargs.get('force_insert')
                and not cls.get_or_none(cls.id == self.id)):
            kwargs['force_insert'] = True
        return super().save(*args, **kwargs)

    @final
    def cascade_save(self, *args, **kwargs):
        """Saves the object and all other objects that are part of it
        (foreign keys pointing to it with on_delete='CASCADE')."""
        self.save(*args, **kwargs)
        for obj in self.cascading_objects():
            obj.cascade_save()

    @classmethod
    def get_model_kwargs(cls, kwargs: dict[str, Any]):
        """Gets a dictionary of keyword arguments, and returns a filtered
        version with only the ones that are needed to instantiate the model."""
        return {k: v for k, v in kwargs.items()
                if k in cls._meta.sorted_field_names}

    def data_dict(self):
        return model_to_dict(self, recurse=False)

    class Meta:
        database = db
        legacy_table_names = False

    @classmethod
    def cascading_fld_names(cls) -> Iterable[str]:
        for name, hint in get_type_hints(cls).items():
            try:
                if hint.__origin__ == CascadingBackref:
                    yield name
            except AttributeError:
                pass

    def cascading_objects(self) -> list[_BaseModel]:
        objects = []
        for fld_name in self.cascading_fld_names():
            objects += self.__getattribute__(fld_name)
        return objects


class Substrate(_BaseModel):
    name = CharField(unique=True)
    comment = CharField(null=True)

    layers: CascadingBackref[SubstrateLayer]

    def __init__(self, name: str, comment: str, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @classmethod
    def already_taken_names(cls):
        query = Substrate.select(
            Substrate.name
        ).dicts()
        names = [row[Substrate.name.name]
                 # Name of the name field (which is 'name'),
                 # not the name of the substrate.
                 for row in query]
        return names

    def libraries(self) -> set[Library]:
        libraries = (Library
                     .select()
                     .join(Film, on=(Film.library == Library.id))
                     .where(Film.substrate == self))
        return set(libraries)

    def can_be_deleted(self):
        return len(self.libraries()) == 0

    def url(self):
        page_name = 'inspect_substrate.py'.removesuffix('.py')
        # noinspection HttpUrlsUsage
        return f"http://{DOMAIN}/{page_name}?{SUB_ID_URL_KEY}={self.id}"


class SubstrateLayer(_BaseModel):
    thickness = FloatField(null=True)
    h = IntegerField(null=True)
    k = IntegerField(null=True)
    l = IntegerField(null=True)
    position_from_back = IntegerField()
    substrate = ForeignKeyField(Substrate, on_delete='CASCADE',
                                backref='layers')

    stoichio: CascadingBackref[StoichioElement]

    def __init__(self, thickness: float | None, h: int | None, k: int | None,
                 l: int | None, substrate: Substrate | None,
                 position_from_back: int | None, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @classmethod
    def from_stoichio(cls, stoichio: str, thickness: float | None,
                      h: int | None, k: int | None,
                      l: int | None, substrate: Substrate | None,
                      position_from_back: int | None):
        init_kwargs = cls.get_model_kwargs(locals())
        layer = SubstrateLayer(**init_kwargs)
        layer.stoichio = StoichioElement.from_str(
            stoichio, StoichioElement.substrate_layer, layer
        )
        return layer

    def crystal_struct_str(self) -> str | None:
        if self.h is None:
            return None
        else:
            return f'({self.h} {self.k} {self.l})'


class Target(_BaseModel):
    made_on = DateField()
    made_by_email = CharField()
    physical_name = CharField(unique=True)
    previous_version = ForeignKeyField(
        'self', null=True, on_delete='SET NULL', backref='next_version')

    states: CascadingBackref[DeteriorationState]

    uses: Backref[TargetUse]

    def __init__(self, made_on: datetime, made_by_email: str,
                 physical_name: str, previous_version: Target|None,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @classmethod
    def already_taken_names(cls):
        query = Target.select(
            Target.physical_name
        ).dicts()
        names = [row[Target.physical_name.name]
                 for row in query]
        return names

    def get_last_state(self) -> DeteriorationState:
        return (DeteriorationState.select()
                .where(DeteriorationState.target == self)
                .order_by(DeteriorationState.date.desc())
                .first())

    @classmethod
    def from_name(cls, name: str) -> Self:
        return Target.get(Target.physical_name == name)

    def libraries(self) -> set[Library]:
        return set.union(*(state.libraries() for state in self.states))

    def url(self):
        page_name = 'inspect_target.py'.removesuffix('.py')
        # noinspection HttpUrlsUsage
        return f"http://{DOMAIN}/{page_name}?{TARGET_ID_URL_KEY}={self.id}"

    def can_be_deleted(self):
        return len(self.uses) == 0

    def comments(self) -> list[tuple[datetime, str]]:
        return [(state.date, state.comment) # noqa Wrong warning.
                for state in self.states
                if state.comment is not None]


# class Disc(BaseModel):
#     center_px_x = FloatField()
#     center_px_y = FloatField()
#     radius_in_px = FloatField()
#     patch = ForeignKeyField(Patch, on_delete='CASCADE', backref='disc')
#
#     @classmethod
#     def new(cls, center_px_x: float, center_px_y: float, radius_in_px: float,
#             patch: Patch):
#         init_kwargs = self.get_init_kwargs(locals())
#         super().__init__(*args, **model_kwargs, **kwargs)
#
#     def __str__(self):
#         return (f"Center: ({self.center_px_x:g}, {self.center_px_y:g})"
#                 f"  |  Radius: {self.radius_in_px:g}")
#
#     @classmethod
#     def from_circumference_points(cls, points: list[tuple[int, int]],
#                                   patch: Patch) -> Self:
#         assert len(points) == 3, \
#             f"Circumference must contain exactly 3 points. Got {len(points)}."
#         (cx, cy), r = cls.circumference_points_to_center_and_radius(*points)
#         return cls(cx, cy, r, patch)
#
#     Point = tuple[float, float]
#
#     @staticmethod
#     def circumference_points_to_center_and_radius(
#             p1: Disc.Point, p2: Disc.Point, p3: Disc.Point) \
#             -> tuple[Disc.Point, float]:
#         """
#         Given three (X, Y) points on a circle's circumference,
#         returns the (X, Y) center and radius of the circle.
#         """
#         ax, ay = p1
#         bx, by = p2
#         cx, cy = p3
#
#         d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
#         if d == 0:
#             raise ValueError("The three points are collinear "
#                              "— no unique circle exists.")
#         ux = (
#                      (ax ** 2 + ay ** 2) * (by - cy)
#                      + (bx ** 2 + by ** 2) * (cy - ay)
#                      + (cx ** 2 + cy ** 2) * (ay - by)
#              ) / d
#         uy = (
#                      (ax ** 2 + ay ** 2) * (cx - bx)
#                      + (bx ** 2 + by ** 2) * (ax - cx)
#                      + (cx ** 2 + cy ** 2) * (bx - ax)
#              ) / d
#
#         radius = ((ax - ux) ** 2 + (ay - uy) ** 2) ** 0.5
#         return (ux, uy), radius

# class Polygon(BaseModel):
#     patch = ForeignKeyField(Patch, on_delete='CASCADE', backref='polygon')
#
#     vertices: list[Vertex]
#
#     @classmethod
#     def new(cls, patch: Patch):
#         init_kwargs = self.get_init_kwargs(locals())
#         super().__init__(*args, **model_kwargs, **kwargs)


#
#     def __str__(self):
#         str_ = 'Vertices:'
#         for v in self.ordered_vertices():
#             str_ += f' {v}'
#         return str_
#
#     def ordered_vertices(self) -> list[Vertex]:
#         def get_rank(v: Vertex):
#             return int(v.clockwise_rank)  # noqa I don't understand the warning.
#
#         return sorted(self.vertices, key=get_rank)
#
#     def to_scatter(self, color: str, name: str) -> Scatter:
#         vertex_list: list[tuple[float, float]] = [
#             (v.pixel_x, v.pixel_y)
#             for v in self.ordered_vertices()
#         ]
#         if vertex_list[-1] != vertex_list[0]:
#             vertex_list.append(vertex_list[0])  # Close de loop.
#         x_list, y_list = zip(*vertex_list)
#         return Scatter(
#             x=x_list, y=y_list,
#             mode='lines',
#             fill='toself',
#             fillcolor=color,
#             opacity=1,
#             line=dict(width=1, color='black'),
#             showlegend=False,
#             name=name,
#         )
#
#     @classmethod
#     def from_text(cls, text: str, patch: Patch) -> Self:
#         vertex_tuples = cls.polygon_text_to_vertices(text)
#         polygon = Polygon.from_ordered_vertices(vertex_tuples, patch)
#         return polygon
#
#     @staticmethod
#     def polygon_text_to_vertices(text: str) -> list[tuple[float, float]]:
#         """
#         The input must be a list of vertices, one on each line. Each vertex
#         is an X,Y couple. Example of a triangle: 12.3, 48.3 78, 15.6 6.1, 5
#         """
#         text = (text
#                 .replace(' ', '')  # Removes all white spaces.
#                 .strip(',\n')  # Allow dots at the start or end.
#                 )
#         vertex_lines = filter(None, text.split('\n')) # Removes empty as well.
#         vertex_tuples: list[tuple[float, float]] = []
#         for vertex_line in vertex_lines:
#             x, y = vertex_line.removesuffix(',').split(',')
#             vertex_tuples.append((float(x), float(y)))
#         return vertex_tuples
#
#     @classmethod
#     def from_ordered_vertices(cls,
#                               clockwise_vertices: list[tuple[float, float]],
#                               patch: Patch) -> Self:
#         polygon = cls(patch=patch)
#         vertices = []
#         for i, (x, y) in enumerate(clockwise_vertices):
#             vertices.append(
#                 Vertex(pixel_x=x, pixel_y=y, clockwise_rank=i,
#                            polygon=polygon))
#         polygon.vertices = vertices
#         return polygon
#
#     @classmethod
#     def from_aligned_rectangle_data(cls, first_vertex: tuple[float, float],
#                                     opposite_vertex: tuple[float, float],
#                                     patch: Patch) -> Self:
#         return Polygon.from_ordered_vertices(
#             [
#                 (first_vertex[0], first_vertex[1]),
#                 (first_vertex[0], opposite_vertex[1]),
#                 (opposite_vertex[0], opposite_vertex[1]),
#                 (opposite_vertex[0], first_vertex[1]),
#             ],
#             patch=patch,
#         )


class MokeCoilFactor(_BaseModel):
    validity_start = DateField()
    validity_end = DateField()
    factor = FloatField()
    comment = CharField(null=True)

    def __init__(self, validity_start: datetime, validity_end: datetime,
                 factor: float, comment: str, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class EsrfPoni(_BaseModel):
    validity_start = DateField()
    validity_end = DateField()
    distance = FloatField()
    poni1 = FloatField()
    poni2 = FloatField()
    rot1 = FloatField()
    rot2 = FloatField()
    rot3 = FloatField()
    wavelength = FloatField()
    comment = CharField(null=True)

    def __init__(self, validity_start: datetime, validity_end: datetime,
                 distance: float, poni1: float,
                 poni2: float, rot1: float, rot2: float, rot3: float,
                 wavelength: float, comment: str, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class Library(_BaseModel):
    name = CharField(unique=True)
    last_inspected_at = DateTimeField()
    comment = CharField(null=True)
    hdf5_file_name = CharField(null=True)

    uploaded_files: CascadingBackref[UserUploadedFile]
    film: CascadingBackref[Film]  # Should be a list of exactly 1 element.

    # Will add charac refs in the future.

    def __init__(self, name: str, last_inspected_at: datetime, comment: str,
                 hdf5_file_name: str | None, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    # def cascading_children_obsolete(self) -> list[BaseModel]:
    #     return self.film + self.uploaded_files

    @classmethod
    def already_taken_names(cls):
        query = cls.select(
            cls.name
        ).dicts()
        names = [row[cls.name.name]
                 for row in query]
        return names

    def get_url(self):
        page_name = 'inspect_library.py'.removesuffix('.py')
        # noinspection HttpUrlsUsage
        return f"http://{DOMAIN}/{page_name}?{LIB_ID_URL_KEY}={self.id}"

    @staticmethod
    def dependent_libraries():
        return []  # TODO Implement this.

    def can_be_deleted(self):
        return len(self.dependent_libraries()) == 0


class Film(_BaseModel):
    physical_name = CharField(unique=True)
    made_on = DateField()
    made_by_email = CharField()
    substrate = ForeignKeyField(Substrate)
    library = ForeignKeyField(Library, on_delete='CASCADE', backref='film')

    layers: CascadingBackref[FilmLayer]
    modifs: CascadingBackref[FilmModification]

    # Will add characterization.

    def __init__(self, physical_name: str, made_on: datetime,
                 made_by_email: str,
                 substrate: Substrate, library: Library,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    # def cascading_children_obsolete(self) -> list[BaseModel]:
    #     return self.layers + self.modifs

    @classmethod
    def already_taken_names(cls):
        query = Film.select(
            Film.physical_name
        ).dicts()
        names = [row[Film.physical_name.name]
                 for row in query]
        return names

    def ordered_modifs(self) -> list[FilmModification]:
        modifs = FilmModification.select().where(
            FilmModification.film == self)

        def get_modif_nb(fm: FilmModification):
            return int(fm.modif_number)  # noqa

        return sorted(list(modifs), key=get_modif_nb)


class FilmLayer(_BaseModel):
    position_from_buffer = IntegerField()
    deposit_temp = FloatField(null=True)
    nominal_thickness = FloatField(null=True)
    shadow_mask_description = CharField(null=True)
    function: FilmLayerFunction = CharField()
    sputtering_system: SputteringSystem = CharField(null=True)

    film = ForeignKeyField(Film, on_delete='CASCADE', backref='layers')

    stoichio: CascadingBackref[StoichioElement]
    target_uses: CascadingBackref[TargetUse]
    magnetron_sputtering: CascadingBackref[MagnetronSputtering]
    triode_sputtering: CascadingBackref[TriodeSputtering]

    def __init__(self, position_from_buffer: int | None,
                 deposit_temp: float | None,
                 nominal_thickness: float | None,
                 shadow_mask_description: str | None,
                 function: FilmLayerFunction,
                 sputtering_system: SputteringSystem | None, film: Film,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def elements(self):
        return set(e.element for e in self.stoichio)


class MagnetronSputtering(_BaseModel):
    deposit_distance = FloatField(null=True)
    deposit_angle = FloatField(null=True)
    deposit_power = FloatField(null=True)
    deposit_duration = FloatField(null=True)
    generator: MagnetronSputteringGenerator = CharField(null=True)
    machine_model: MagnetronMachineModel = CharField(null=True)

    film_layer = ForeignKeyField(FilmLayer, on_delete='CASCADE',
                                 backref='magnetron_sputtering')

    def __init__(self, deposit_distance: float | None,
                 deposit_angle: float | None,
                 deposit_power: float | None, deposit_duration: float | None,
                 generator: MagnetronSputteringGenerator | None,
                 machine_model: MagnetronMachineModel | None,
                 film_layer: FilmLayer, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class TriodeSputtering(_BaseModel):
    has_active_cooling = BooleanField(null=True)
    rotation = FloatField(null=True)
    filament_current = FloatField(null=True)
    anode_current = FloatField(null=True)
    anode_voltage = FloatField(null=True)
    cathode_current = FloatField(null=True)
    cathode_voltage = FloatField(null=True)
    deposit_rate = FloatField(null=True)
    argon_flow = FloatField(null=True)
    nitrogen_flow = FloatField(null=True)
    pressure = FloatField(null=True)
    deposit_duration = FloatField(null=True)
    presputtering_thickness = FloatField(null=True)

    film_layer = ForeignKeyField(FilmLayer, on_delete='CASCADE',
                                 backref='triode_sputtering')

    def __init__(self,
                 has_active_cooling: bool | None,
                 rotation: float | None,
                 filament_current: float | None,
                 anode_current: float | None,
                 anode_voltage: float | None,
                 cathode_current: float | None,
                 cathode_voltage: float | None,
                 deposit_rate: float | None,
                 argon_flow: float | None,
                 nitrogen_flow: float | None,
                 pressure: float | None,
                 deposit_duration: float | None,
                 presputtering_thickness: float | None,
                 film_layer: FilmLayer,
                 *args, **kwargs
                 ):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class UserUploadedFile(_BaseModel):
    file_name = CharField(unique=True)
    library = ForeignKeyField(Library, on_delete='CASCADE',
                              backref='uploaded_files')

    def __init__(self, file_name: str, library: Library, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @classmethod
    def from_streamlit_uploaded_file(
            cls, upload_field: UploadedFile,
            library: Library) -> UserUploadedFile:
        extension = upload_field.name.split('.')[-1]
        file_name = f'{uuid4()}.{extension}'
        return cls(file_name=file_name, library=library)


class FilmModification(_BaseModel):
    made_on = DateField()
    modif_number = IntegerField()
    made_by_email = CharField()
    comment = CharField(null=True)
    modif_type: FilmModifType = CharField()

    film = ForeignKeyField(Film, on_delete='CASCADE', backref='modifs')

    annealing: CascadingBackref[Annealing]
    wet_etching: CascadingBackref[WetEtching]
    ion_beam_etching: CascadingBackref[IonBeamEtching]
    lift_off: CascadingBackref[LiftOff]

    # Will add characs in the future.

    def __init__(self, made_on: datetime, modif_number: int, made_by_email: str,
                 comment: str, modif_type: FilmModifType, film: Film,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def save(self, shift_subsequent_modifs=True):
        """Saves a film modification with its modif_number, and adds 1 to all
        modif_number attributes of subsequent film modifications."""
        if shift_subsequent_modifs:
            for modif in FilmModification.select():
                if modif.modif_number >= self.modif_number:
                    modif.modif_number += 1
                    modif.save(shift_subsequent_modifs=False)
        super().save()

    def delete_instance(self, recursive=..., delete_nullable=...):
        """Saves a film modification with its modif_number, and adds 1 to all
        modif_number attributes of subsequent film modifications."""
        for modif in FilmModification.select():
            if modif.modif_number >= self.modif_number:
                modif.modif_number -= 1
                modif.save(shift_subsequent_modifs=False)
        super().delete_instance()

    def modification_process(self) \
            -> (Annealing | WetEtching | LiftOff |
                IonBeamEtching):
        fmt = FilmModifType
        match self.modif_type:
            case fmt.ANNEALING:
                return self.annealing[0]
            case fmt.WET_ETCHING:
                return self.wet_etching[0]
            case fmt.ION_BEAM_ETCHING:
                return self.ion_beam_etching[0]
            case fmt.LIFT_OFF:
                return self.lift_off[0]


class LiftOff(_BaseModel):
    used_ultrasound = BooleanField(null=True)
    ultrasound_config = CharField(null=True)
    pattern_diagram_file_name = CharField(null=True)
    recipe_file_name = CharField(null=True)

    film_modif = ForeignKeyField(FilmModification, on_delete='CASCADE',
                                 backref='lift_off')

    def __init__(self, used_ultrasound: bool | None,
                 ultrasound_config: str | None,
                 pattern_diagram_file_name: str | None,
                 recipe_file_name: str | None,
                 film_modif: FilmModification, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def image_path(self):
        return Path(PATTERN_IMAGE_PATH) / str(self.pattern_diagram_file_name)


class Annealing(_BaseModel):
    pressure = FloatField(null=True)
    pumping_duration = FloatField(null=True)
    furnace: Furnace = CharField(null=True)
    film_modif = ForeignKeyField(FilmModification, on_delete='CASCADE')

    steps: CascadingBackref[AnnealingStep]

    def __init__(self, pumping_duration: float | None, pressure: float | None,
                 furnace: Furnace | None,
                 film_modif: FilmModification, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class AnnealingStep(_BaseModel):
    elapsed = FloatField()
    temperature = FloatField()

    annealing = ForeignKeyField(Annealing, on_delete='CASCADE',
                                backref='steps')

    atmosphere: CascadingBackref[StoichioElement]

    def __init__(self, elapsed: float, temperature: float,
                 annealing: Annealing, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class IonBeamEtching(_BaseModel):
    duration = FloatField(null=True)
    flow = FloatField(null=True)
    incidence_angle = FloatField(null=True)
    rotation = FloatField(null=True)
    power = FloatField(null=True)
    pressure = FloatField(null=True)
    has_a_pattern = BooleanField(null=True)
    pattern_diagram_file_name = CharField(null=True)

    film_modif = ForeignKeyField(FilmModification, on_delete='CASCADE')

    constituents: CascadingBackref[PlasmaConstituent]

    def __init__(self, duration: float | None, flow: float | None,
                 incidence_angle: float | None, rotation: float | None,
                 power: float | None, pressure: float | None,
                 has_a_pattern: bool | None,
                 pattern_diagram_file_name: str | None,
                 film_modif: FilmModification | None, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def image_path(self):
        return Path(PATTERN_IMAGE_PATH) / str(self.pattern_diagram_file_name)


class PlasmaConstituent(_BaseModel):
    proportion = FloatField()

    etching = ForeignKeyField(IonBeamEtching, on_delete='CASCADE',
                              backref='constituents')

    stoichio: CascadingBackref[StoichioElement]

    def __init__(self, proportion: float, etching: IonBeamEtching,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class WetEtching(_BaseModel):
    hard_bake_temperature = FloatField(null=True)
    acid_etching_duration = FloatField(null=True)
    acid_etching_comment = CharField(null=True)
    used_ultrasound = BooleanField(null=True)
    ultrasound_config = CharField(null=True)
    acid_etching_depth_speed = FloatField(null=True)
    acid_etching_lateral_speed = FloatField(null=True)
    has_a_pattern = BooleanField(null=True)
    pattern_diagram_file_name = CharField(null=True)
    recipe_file_name = CharField(null=True)

    film_modif = ForeignKeyField(FilmModification, on_delete='CASCADE')

    constituents: CascadingBackref[AcidConstituent]

    def __init__(self,
                 hard_bake_temperature: float | None,
                 acid_etching_duration: float | None,
                 acid_etching_comment: str | None,
                 used_ultrasound: bool | None,
                 ultrasound_config: str | None,
                 acid_etching_depth_speed: float | None,
                 acid_etching_lateral_speed: float | None,
                 has_a_pattern: bool | None,
                 pattern_diagram_file_name: str | None,
                 recipe_file_name: str | None,
                 film_modif: FilmModification,
                 *args, **kwargs
                 ):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class AcidConstituent(_BaseModel):
    proportion = FloatField()

    etching = ForeignKeyField(WetEtching, on_delete='CASCADE',
                              backref='constituents')

    stoichio: CascadingBackref[StoichioElement]

    def __init__(self, proportion: float, etching: WetEtching, *args,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class DeteriorationState(_BaseModel):
    date = DateField(unique=True)
    made_by_email = CharField()
    px_to_real_length_factor = FloatField(null=True)
    photo_file_name = CharField(null=True)
    calibration_factor = FloatField(null=True)
    comment = CharField(null=True)
    pixel_coordinate_system: PixelCoordinateSystem = CharField(null=True)

    target = ForeignKeyField(Target, on_delete='CASCADE', backref='states')

    patches: CascadingBackref[Patch]

    def __init__(self, date: datetime, px_to_real_length_factor: float | None,
                 photo_file_name: str | None, calibration_factor: float | None,
                 comment: str | None,
                 pixel_coordinate_system: PixelCoordinateSystem | None,
                 target: Target, made_by_email: str,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def photo_path(self):
        return FILE_STORAGE_PATH / self.photo_file_name

    def libraries(self) -> set[Library]:
        libs = (
            Library
            .select()
            .join(Film, on=(Film.library == Library.id))
            .join(FilmLayer, on=(FilmLayer.film == Film.id))
            .join(TargetUse,
                  on=(TargetUse.film_layer == FilmLayer.id))
            .where(TargetUse.target == self))
        return set(libs)

    @staticmethod
    def empty_figure():
        return go.Figure(
            [Scatter()],
            layout=go.Layout(
                xaxis={'showgrid': True, 'side': 'top'},
                yaxis={'scaleanchor': 'x', 'autorange': 'reversed'},
            ),
        )

    def to_figure(self):
        fig = self.empty_figure()
        for patch in self.patches:
            scatter = patch.to_scatter()
            fig.add_trace(scatter)
        return fig


# TODO assert all FK have a backref.
# TODO assert all the unique are correct.


class Patch(_BaseModel):
    stack_idx = IntegerField()

    deterioration_state = ForeignKeyField(DeteriorationState,
                                          on_delete='CASCADE',
                                          backref='patches')

    stoichio: CascadingBackref[StoichioElement]
    vertices: CascadingBackref[Vertex]

    def __init__(self, stack_idx: int,
                 deterioration_state: DeteriorationState,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def __str__(self):
        return f'Patch of stoichiometry {self.stoichio}'

    @classmethod
    def from_polygon(cls, stoichio_str: str,
                     vertices: VertexList,
                     stack_idx: int,
                     deterioration_state: DeteriorationState) \
            -> Patch:
        patch = cls(stack_idx, deterioration_state)
        patch.stoichio = StoichioElement.from_str(
            formula=stoichio_str,
            fk_field=StoichioElement.patch,
            parent=patch,
        )
        patch.vertices = [
            Vertex(pixel_x=x, pixel_y=y, clockwise_rank=i, patch=patch)
            for i, (x, y) in enumerate(vertices)
        ]
        return patch

    @staticmethod
    def is_valid_formula(stoichio_str: str) -> tuple[bool, str]:
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

    def plotly_color(self, stoichio_str: str = None):
        if stoichio_str is None:
            stoichio_str = StoichioElement.complete_stoichio(self.stoichio)
        r, g, b = Patch.rgb_color(stoichio_str)
        return f'rgba({r},{g},{b},1)'

    @staticmethod
    def colored_rectangle_html(stoichio_str: str):
        r, g, b = Patch.rgb_color(stoichio_str)
        return f'<span style="color:rgb({r},{g},{b})">▮</span>'

    def ordered_vertices(self) -> list[Vertex]:
        def get_rank(v: Vertex):
            return int(v.clockwise_rank)  # noqa I don't understand the warning.

        return sorted(self.vertices, key=get_rank)

    # @staticmethod
    # def data_to_scatter(stoichio: str,
    #                     ordered_vertices: list[tuple[float, float]]) \
    #         -> Scatter:
    #     color = PatchModel.plotly_color()
    #     return polygon_patch_to_scatter(ordered_vertices, color_=color,
    #                                     name_=stoichio)

    def to_scatter(self):
        vertices = list(self.vertices)
        # Closing the polygon:
        vertices.append(vertices[0])
        stoichio_str = StoichioElement.complete_stoichio(self.stoichio)

        x_coords, y_coords = zip(*vertices)
        return Scatter(
            x=x_coords, y=y_coords,
            mode='lines',
            fill='toself',
            fillcolor=self.plotly_color(stoichio_str),
            opacity=1,
            line=dict(width=1, color='black'),
            showlegend=False,
            name=stoichio_str,
        )


# @classmethod
# def from_patch_text(cls, text: str,
#                     deterioration_state: DeteriorationState) \
#         -> list[Self]:
#     text = text.replace(' ', '')
#     lines = text.split('\n')
#     lines = [l for l in lines if l != '']  # Remove empty lines.
#     assert len(lines) >= 1, f"Patch data cannot be empty. Got '{lines}'."
#     return [cls._from_text_line(line, deterioration_state, i)
#             for i, line in enumerate(lines)]
#
# @classmethod
# def _from_text_line(cls, line: str, deterioration_state: DeteriorationState,
#                     stack_idx: int) \
#         -> Self:
#     line = line.replace(' ', '').removesuffix('/')
#     text_elements: list[str] = line.split('/')
#     assert len(text_elements) >= 5, f"Not enough info on the line: {line}"
#     shape_type_str = text_elements[0].lower()
#     try:
#         shape_type = ShapeType(shape_type_str)
#     except ValueError:
#         msg = (f"Each line must start with a valid shape name. "
#                f"Got '{shape_type_str}' instead.")
#         raise ValueError(msg)
#     stoichio = text_elements[1]
#     is_valid, msg = cls.is_valid_formula(stoichio)
#     assert is_valid, f"Invalid stoichiometry for line '{line}'."
#     coord_strings = text_elements[2:]
#     coords: list[tuple[int, int]] = []
#     for s in coord_strings:
#         try:
#             x, y = make_tuple(s)
#         except (ValueError, SyntaxError):
#             raise RuntimeError(f"Invalid coordinates '{s}'.")
#         assert isinstance(x, int) and isinstance(y, int), \
#             f'Pixel coordinates must be integers. Got {x},{y} instead.'
#         assert x >= 0 and y >= 0, f"Coordinates must be positive."
#         coords.append((x, y))
#
#     match shape_type:
#         case ShapeType.DISC:
#             return cls.from_circumference_points(coords, stoichio,
#                                                  stack_idx,
#                                                  deterioration_state)
#         case ShapeType.POLYGON:
#             return cls.from_vertices(stoichio, coords, stack_idx,
#                                      deterioration_state)


class Vertex(_BaseModel):
    pixel_x: float = FloatField()
    pixel_y: float = FloatField()
    clockwise_rank = IntegerField()

    patch = ForeignKeyField(Patch, on_delete='CASCADE', backref='vertices')

    def __init__(self, pixel_x: float, pixel_y: float, clockwise_rank: int,
                 patch: Patch, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def __str__(self):
        return f'({self.pixel_x:g}, {self.pixel_y:g})'

    def __iter__(self):
        return iter([self.pixel_x, self.pixel_y])


class TargetUse(_BaseModel):
    target = ForeignKeyField(Target, backref='uses')
    film_layer = ForeignKeyField(FilmLayer, on_delete='CASCADE',
                                 backref='target_uses')

    def __init__(self, deterioration_state: DeteriorationState,
                 film_layer: FilmLayer,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class StoichioElement(_BaseModel):
    """Can be the stoichiometry of either of these foreign keys."""
    quantity = FloatField()
    position_in_str = IntegerField()
    element: ChemicalElement = CharField()

    substrate_layer = ForeignKeyField(
        SubstrateLayer, null=True, on_delete='CASCADE',
        backref='stoichio')
    patch = ForeignKeyField(
        Patch, null=True, on_delete='CASCADE',
        backref='stoichio')
    film_layer = ForeignKeyField(
        FilmLayer, null=True, on_delete='CASCADE',
        backref='nominal_stoichio')
    annealing_step = ForeignKeyField(
        AnnealingStep, null=True, on_delete='CASCADE',
        backref='atmosphere')
    acid_constituent = ForeignKeyField(
        AcidConstituent, null=True, on_delete='CASCADE',
        backref='stoichio')
    plasma_constituent = ForeignKeyField(
        PlasmaConstituent, on_delete='CASCADE', null=True,
        backref='stoichio')

    def __init__(self, quantity: float, position_in_str: int,
                 element: ChemicalElement,
                 substrate_layer: SubstrateLayer = None,
                 patch: Patch = None, film_layer: FilmLayer = None,
                 annealing: Annealing = None,
                 acid_constituent: AcidConstituent = None,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @classmethod
    def from_str(cls, formula: str, fk_field: ForeignKeyField,
                 parent: _BaseModel
                 ) -> list[StoichioElement]:
        parsed = chemparse.parse_formula(formula)
        elements = [
            StoichioElement(
                quantity=quantity,
                position_in_str=i,
                element=ChemicalElement(short_name),
                **{fk_field.name: parent}
            )
            for i, (short_name, quantity) in enumerate(parsed.items())
        ]
        return elements

    def __str__(self):
        return f'{self.element}{self.quantity:g}'

    @staticmethod
    def complete_stoichio(elements: list[StoichioElement]) -> str:
        def key(element: StoichioElement):
            return int(element.position_in_str)  # noqa

        sorted_elements = sorted(elements, key=key)
        return ''.join([str(e) for e in sorted_elements])


def all_models():
    def is_a_model(cls):
        return (
                inspect.isclass(cls)
                and issubclass(cls, _BaseModel)
                and not cls.__name__.startswith('_')
        )

    name_models = inspect.getmembers(sys.modules[__name__], is_a_model)
    return [model for name, model in name_models]
