import inspect
import sys
from datetime import datetime
from pathlib import Path
from random import Random
from time import sleep
from typing import Self, get_type_hints, Iterable, Any, final

import chemparse
import plotly.graph_objects as go
import streamlit as st
from pandas import DataFrame
from peewee import PostgresqlDatabase, CharField, DateTimeField, \
    ForeignKeyField, FloatField, IntegerField, \
    BooleanField, DateField
from pint.registry import Quantity
from playhouse.shortcuts import model_to_dict  # noqa
from playhouse.signals import Model
from plotly import express as px
from plotly.graph_objs import Scatter, Figure
from pyparsing import alphanums

from logic.constants import FILE_STORAGE_PATH, DOMAIN, \
    ROOM_TEMPERATURE_CELSIUS, IdType, USER_UPLOAD_PATH
from logic.db_enums import SputteringSystem, FilmLayerFunction, \
    MagnetronSputteringGenerator, FilmModifType, Furnace, \
    MagnetronMachineModel, PixelCoordinateSystem, ChemicalElement
from logic.functions import letter_count
from logic.lab_modelization.other_classes import MixtureConstituent
from logic.math_tools import VertexList
from logic.page_list import pages
from logic.python_tools import remove_digits, remove_random_prefix
from logic.units import ur, db_units

# FIELD TYPES:
# https://docs.peewee-orm.com/en/latest/peewee/models.html#fields

db = PostgresqlDatabase(
    'dahu2', user='postgres', password='postgres', host='localhost', port=5432
)

# Be careful, if an attribute is a foreignkey, you have to add '_id' at the
# end of the name of the column, in the DB table. This is because in the
# table, the key is actually store as an ID. The Model.create method is
# overridden to have argument autocompletion.


type DependentBackref[T] = list[T]
type Backref[T] = list[T]


class _BaseModel(Model):
    id: int | IntegerField

    # A list of attributes with title, corresponding attribute and input field.
    title_db_value_input_fields: list[tuple[str, Any, type]] = None

    class Meta:
        database = db
        legacy_table_names = False

    @final
    def save_with_dependent(self, *args, **kwargs):
        """Saves the object and all other objects that dependent on it.
        An object A depends on an object B if A has a foreign key towards B
        with de parameter [on_delete='RESTRICT'] or [on_delete='CASCADE'].
        If the parameter is [on_delete='SET NULL'], which means the foreign
        key can point to nothing, A does not dependent on B."""

        self.save(*args, **kwargs)
        for obj in self.dependent_objects():
            obj.save_with_dependent()

    @classmethod
    def get_model_kwargs(cls, kwargs: dict[str, Any]):
        """Gets a dictionary of keyword arguments, and returns a filtered
        version with only the ones that are needed to instantiate the model."""
        return {k: v for k, v in kwargs.items()
                if k in cls._meta.sorted_field_names}

    @classmethod
    def dependent_object_fld_names(cls) -> Iterable[str]:
        for name, hint in get_type_hints(cls).items():
            try:
                if hint.__origin__ == DependentBackref:
                    yield name
            except AttributeError:
                pass

    def dependent_objects(self) -> list[_BaseModel]:
        objects = []
        for fld_name in self.dependent_object_fld_names():
            new_objects = self.__getattribute__(fld_name)
            objects += list(new_objects)
        return objects

    def data_string(self, separator='\n\n'):
        from components.forms.base_classes import UnitField
        if self.title_db_value_input_fields is None:
            raise RuntimeError('self.title_db_value_input_fields is not set.')
        description_items = []
        for title, db_value, field in self.title_db_value_input_fields:
            try:
                field: UnitField
                quantity_str = field.db_to_ui_str(db_value) \
                    if db_value is not None else '_None_'
            except AttributeError:
                quantity_str = db_value if db_value is not None else '_None_'
            description_items.append(f"**{title}:** {quantity_str}")
        return separator.join(description_items)


class Substrate(_BaseModel):
    label = CharField(unique=True)
    comment = CharField(null=True)

    layers: DependentBackref[SubstrateLayer]

    def __init__(self, label: str, comment: str, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @classmethod
    def already_taken_names(cls):
        query = Substrate.select(
            Substrate.label
        ).dicts()
        names = [row[Substrate.label.name]
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
        page_name = pages.inspect_substrate.url_path
        # noinspection HttpUrlsUsage
        return f"http://{DOMAIN}/{page_name}?{IdType.SUB}={self.id}"

    @classmethod
    def from_label(cls, label: str) -> Self:
        return Substrate.get(Substrate.label == label)


class SubstrateLayer(_BaseModel):
    thickness = FloatField(null=True)
    h = IntegerField(null=True)
    k = IntegerField(null=True)
    l = IntegerField(null=True)
    position_from_back = IntegerField()
    substrate: Substrate = ForeignKeyField(Substrate, on_delete='RESTRICT',
                                           backref='layers')

    stoichio: DependentBackref[StoichioElement]

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
    label: str | ForeignKeyField = CharField(unique=True)
    previous_version: Target = ForeignKeyField(
        'self', null=True, on_delete='SET NULL', backref='next_version')

    states: DependentBackref[DeteriorationState]
    uses: DependentBackref[TargetUse]

    def __init__(self, made_on: datetime, made_by_email: str,
                 label: str, previous_version: Target | None,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @classmethod
    def already_taken_names(cls):
        query = Target.select(
            Target.label
        ).dicts()
        names = [row[Target.label.name]
                 for row in query]
        names = sorted(names, key=lambda name: name)
        return names

    @property
    def last_state(self) -> DeteriorationState:
        return self.old_to_recent_states()[-1]

    def old_to_recent_states(self) -> list[DeteriorationState]:
        return list(DeteriorationState.select()
                    .where(DeteriorationState.target == self)
                    .order_by(DeteriorationState.date.asc()))

    @classmethod
    def from_label(cls, label: str) -> Self:
        return Target.get(Target.label == label)

    def libraries(self) -> set[Library]:
        return set.union(*(state.libraries() for state in self.states))

    def url(self):
        page_name = pages.inspect_target.url_path
        # noinspection HttpUrlsUsage
        return f"http://{DOMAIN}/{page_name}?{IdType.TARGET}={self.id}"

    def can_be_deleted(self):
        return len(self.uses) == 0

    def comments(self) -> list[tuple[datetime, str]]:
        return [(state.date, state.comment)  # noqa Wrong warning.
                for state in self.states
                if state.comment]


# class Disc(BaseModel):
#     center_px_x = FloatField()
#     center_px_y = FloatField()
#     radius_in_px = FloatField()
#     patch = ForeignKeyField(Patch, on_delete='RESTRICT', backref='disc')
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
#     patch = ForeignKeyField(Patch, on_delete='RESTRICT', backref='polygon')
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
    label = CharField(unique=True)
    last_inspected_at = DateTimeField()
    comment = CharField(null=True)

    films: DependentBackref[Film]  # Should be a list of exactly 1 element.

    # Will add charac refs in the future.

    def __init__(self, label: str, last_inspected_at: datetime, comment: str,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    # def cascading_children_obsolete(self) -> list[BaseModel]:
    #     return self.film + self.uploaded_files

    @classmethod
    def already_taken_names(cls):
        query = cls.select(
            cls.label
        ).dicts()
        names = [row[cls.label.name]
                 for row in query]
        return names

    @property
    def url(self):
        page_name = pages.inspect_lib.url_path
        # noinspection HttpUrlsUsage
        return f"http://{DOMAIN}/{page_name}?{IdType.LIB}={self.id}"

    @staticmethod
    def dependent_libraries():
        return []  # TODO Implement this.

    def can_be_deleted(self):
        return len(self.dependent_libraries()) == 0


class Film(_BaseModel):
    label = CharField(unique=True)
    made_on = DateField()
    made_by_email = CharField()
    substrate: Substrate = ForeignKeyField(Substrate)
    library: Library = ForeignKeyField(Library, on_delete='RESTRICT',
                                       backref='films')

    layers: DependentBackref[FilmLayer]
    modifs: DependentBackref[FilmModification]

    # Will add characterization.

    def __init__(self, label: str, made_on: datetime,
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
            Film.label
        ).dicts()
        names = [row[Film.label.name]
                 for row in query]
        return names

    def ordered_modifs(self) -> list[FilmModification]:
        modifs = FilmModification.select().where(
            FilmModification.film == self)

        def get_modif_count(fm: FilmModification):
            return int(fm.modif_number)  # noqa

        return sorted(list(modifs), key=get_modif_count)

    @property
    def ordered_layers(self) -> list[FilmLayer]:
        layers = [l for l in self.layers]

        def position(layer: FilmLayer):
            return layer.position_from_buffer

        return sorted(layers, key=position)

    @property
    def target_labels(self) -> list[str]:
        labels: set[str] = set()
        for l in self.layers:
            for use in l.target_uses:
                labels.add(use.target.label)
        return list(labels)

    @property
    def targets(self) -> list[Target]:
        targets: set[Target] = set()
        for l in self.target_labels:
            target = Target.from_label(l)
            targets.add(target)
        return list(targets)


class FilmLayer(_BaseModel):
    position_from_buffer: int = IntegerField()
    deposit_temp = FloatField(null=True)
    nominal_thickness = FloatField(null=True)
    shadow_mask_description = CharField(null=True)
    function: FilmLayerFunction = CharField()
    sputtering_system: SputteringSystem = CharField(null=True)

    film: Film = ForeignKeyField(Film, on_delete='RESTRICT', backref='layers')
    # target: Target = ForeignKeyField(Target, on_delete='RESTRICT',
    #                          backref='film_layers')

    nominal_stoichio: DependentBackref[StoichioElement]
    target_uses: DependentBackref[TargetUse]
    magnetron_sputterings: DependentBackref[MagnetronSputtering]  # List of 1.
    triode_sputterings: DependentBackref[TriodeSputtering]  # List of 1.

    def __init__(self,
                 position_from_buffer: int | None,
                 deposit_temp: float | None,
                 nominal_thickness: float | None,
                 shadow_mask_description: str | None,
                 function: FilmLayerFunction,
                 sputtering_system: SputteringSystem | None,
                 film: Film,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @property
    def element_str(self) -> str:
        return remove_digits(self.nominal_stoichio_str)

    @property
    def nominal_stoichio_str(self) -> str:
        str_ = StoichioElement.to_str(self.nominal_stoichio)
        assert len(str_) > 0
        return str_

    @property
    def sputtering(self) -> MagnetronSputtering | TriodeSputtering:
        mag_sputters = self.magnetron_sputterings
        triode_sputters = self.triode_sputterings
        if len(mag_sputters) + len(triode_sputters) != 1:
            raise RuntimeError("There must be exactly one sputtering per "
                               "layer.")
        if len(mag_sputters) == 1:
            return mag_sputters[0]
        else:
            return triode_sputters[0]

    @property
    def target_labels(self) -> list[str]:
        return [u.target.label for u in self.target_uses]


class MagnetronSputtering(_BaseModel):
    deposit_distance = FloatField(null=True)
    deposit_angle = FloatField(null=True)
    deposit_power = FloatField(null=True)
    deposit_duration = FloatField(null=True)
    generator: MagnetronSputteringGenerator = CharField(null=True)
    machine_model: MagnetronMachineModel = CharField(null=True)

    film_layer: FilmLayer = ForeignKeyField(FilmLayer, on_delete='RESTRICT',
                                            backref='magnetron_sputterings')

    def __init__(self, deposit_distance: float | None,
                 deposit_angle: float | None,
                 deposit_power: float | None, deposit_duration: float | None,
                 generator: MagnetronSputteringGenerator | None,
                 machine_model: MagnetronMachineModel | None,
                 film_layer: FilmLayer, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @property
    def title_db_value_input_fields(self):
        from components.forms.new_library.fields import DepositDistanceField, \
            DepositAngleField, DepositPowerField, DepositDurationField, \
            MagnetronGeneratorField, MagnetronModelField
        return [
            ('Deposit distance', self.deposit_distance, DepositDistanceField),
            ('Deposit angle', self.deposit_angle, DepositAngleField),
            ('Power', self.deposit_power, DepositPowerField),
            ('Duration', self.deposit_duration, DepositDurationField),
            ('Generator', self.generator, MagnetronGeneratorField),
            ('Machine model', self.machine_model, MagnetronModelField),
        ]


class TriodeSputtering(_BaseModel):
    has_active_cooling = BooleanField(null=True)
    rotation_speed = FloatField(null=True)
    filament_current_start = FloatField(null=True)
    filament_current_end = FloatField(null=True)
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

    film_layer: FilmLayer = ForeignKeyField(FilmLayer, on_delete='RESTRICT',
                                            backref='triode_sputterings')

    def __init__(self,
                 has_active_cooling: bool | None,
                 rotation_speed: float | None,
                 filament_current_start: float | None,
                 filament_current_end: float | None,
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

    @property
    def deposit_power(self) -> float:
        return None  # noqa TODO Can we define a power for triode?

    @property
    def title_db_value_input_fields(self):
        from components.forms.new_library.fields import (
            HasActiveCoolingField, RotationSpeedField,
            FilamentCurrentStartField, FilamentCurrentEndField,
            AnodeCurrentField, AnodeVoltageField, CathodeCurrentField,
            CathodeVoltageField, DepositRateField, ArgonFlowField,
            NitrogenFlowField, PressureField, DepositDurationField,
            PresputteringThicknessField
        )
        return [
            ('Has active cooling', self.has_active_cooling,
                HasActiveCoolingField),
            ('Rotation speed', self.rotation_speed, RotationSpeedField),
            ('Filament current start', self.filament_current_start,
                FilamentCurrentStartField),
            ('Filament current end', self.filament_current_end,
                FilamentCurrentEndField),
            ('Anode current', self.anode_current, AnodeCurrentField),
            ('Anode voltage', self.anode_voltage, AnodeVoltageField),
            ('Cathode current', self.cathode_current, CathodeCurrentField),
            ('Cathode voltage', self.cathode_voltage, CathodeVoltageField),
            ('Deposit rate', self.deposit_rate, DepositRateField),
            ('Argon flow', self.argon_flow, ArgonFlowField),
            ('Nitrogen flow', self.nitrogen_flow, NitrogenFlowField),
            ('Pressure', self.pressure, PressureField),
            ('Deposit duration', self.deposit_duration, DepositDurationField),
            ('Presputtering thickness', self.presputtering_thickness,
                PresputteringThicknessField),
        ]


class UserUploadedFile(_BaseModel):
    label: str = CharField(null=True)
    file_name: str = CharField(unique=True)
    upload_date = DateField()

    _file_bytes: bytes | None = None  # Not in DB.

    def __init__(self, label: str, file_name: str, upload_date: datetime,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def get_path(self):
        return USER_UPLOAD_PATH.joinpath(self.file_name)

    def delete_file(self):
        Path.unlink(self.get_path())
        sleep(.1)

    @property
    def file_bytes(self):
        if self._file_bytes is None:
            try:
                with open(self.get_path(), 'rb') as file:
                    self._file_bytes = file.read()
            except FileNotFoundError:
                self._file_bytes = None
        return self._file_bytes

    @file_bytes.setter
    def file_bytes(self, file_bytes: bytes):
        self._file_bytes = file_bytes

    def retrieve_file_bytes(self):
        with open(self.get_path(), 'rb') as file:
            bytes_ = file.read()
        self.file_bytes = bytes_

    def save_bytes(self):
        with open(self.get_path(), 'wb') as file:
            assert len(self.file_bytes), "File cannot be empty."
            file.write(self.file_bytes)

    def download_bttn(self):
        if self.file_bytes is None:
            st.write('_File missing_')
        else:
            st.download_button(
                label=self.label,
                data=self.file_bytes,
                file_name=remove_random_prefix(self.file_name),
                icon=":material/download:",
            )


class FilmModification(_BaseModel):
    made_on = DateField()
    modif_number = IntegerField()
    made_by_email = CharField()
    comment = CharField(null=True)
    modif_type: FilmModifType = CharField()

    film: Film = ForeignKeyField(Film, on_delete='RESTRICT', backref='modifs')

    annealings: DependentBackref[Annealing]
    etchings: DependentBackref[Etching]

    # Will add characs in the future.

    def __init__(self, made_on: datetime, modif_number: int, made_by_email: str,
                 comment: str, modif_type: FilmModifType, film: Film,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def save(self, shift_subsequent_modifs=True):  # noqa
        """Saves a film modification with its modif_number, and adds 1 to all
        modif_number attributes of subsequent film modifications."""
        if shift_subsequent_modifs:
            for modif in FilmModification.select():
                if modif.modif_number >= self.modif_number:
                    modif.modif_number += 1
                    modif.save(shift_subsequent_modifs=False)
        super().save()

    def delete_instance(self, recursive: bool = False,
                        delete_nullable: bool = False):
        """Saves a film modification with its modif_number, and adds 1 to all
        modif_number attributes of subsequent film modifications."""
        for modif in FilmModification.select():
            if modif.modif_number >= self.modif_number:
                modif.modif_number -= 1
                modif.save(shift_subsequent_modifs=False)

        if self.etchings:
            self.etchings[0].delete_related_files()

        super().delete_instance(recursive, delete_nullable)

    def modification_process(self) \
            -> (Annealing | WetEtching | LiftOffEtching | IonBeamEtching):
        fmt = FilmModifType
        match self.modif_type:
            case fmt.ANNEALING:
                return self.annealings[0]
            case fmt.WET_ETCHING:
                return self.etchings[0].wet_etchings[0]
            case fmt.ION_BEAM_ETCHING:
                return self.etchings[0].ion_etchings[0]
            case fmt.LIFT_OFF:
                return self.etchings[0].lift_offs[0]

    @property
    def previous_modif(self) -> Self:
        if self.modif_number == 0:
            return None
        else:
            return FilmModification.get(
                (FilmModification.film == self.film) &
                (FilmModification.modif_number == self.modif_number - 1)
            )


class Annealing(_BaseModel):
    pressure = FloatField(null=True)
    pumping_duration = FloatField(null=True)
    furnace: Furnace = CharField(null=True)
    film_modif: FilmModification = ForeignKeyField(
        FilmModification, on_delete='RESTRICT', backref='annealings')

    steps: DependentBackref[AnnealingStep]
    atmosphere: list[StoichioElement]

    def __init__(self, pumping_duration: float | None, pressure: float | None,
                 furnace: Furnace | None,
                 film_modif: FilmModification, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @property
    def temperatures(self) -> set[Quantity]:
        return {s.temp_quantity for s in self.steps}

    @property
    def max_temperature(self) -> Quantity:
        return max(self.temperatures)  # noqa Wrong warning.

    @property
    def ordered_steps(self):
        def key(step: AnnealingStep):
            return step.timestamp

        return sorted(self.steps, key=key)

    def save(self, *args, **kwargs):
        self.assert_valid_annealing()
        super().save(*args, **kwargs)

    @property
    def duration(self) -> float:
        steps = self.ordered_steps
        assert steps[0].is_room_temperature and steps[-1].is_room_temperature, (
            f"Annealing must start with and end with room temperature. Got "
            f"respectively {steps[0].temperature} and {steps[-1].temperature} "
            f"instead."
        )
        return steps[-1].timestamp

    def assert_valid_annealing(self):
        steps = self.ordered_steps
        assert len(steps) >= 3, (
            "There must be at least 3 steps: initial (room temp.), "
            "aimed temp. state and end state (room temp. again).")
        assert steps[0].is_room_temperature and steps[-1].is_room_temperature, (
            'First and last steps must be at room temperature.')
        assert steps[0].timestamp == 0, "First step must have timestamp 0."

    @property
    def atmosphere_formula(self):
        return StoichioElement.to_str(self.atmosphere)

    def get_figure(self) -> Figure:
        return AnnealingStep.get_figure(self.steps)


class AnnealingStep(_BaseModel):
    timestamp: float = FloatField()
    temperature: float = FloatField(null=True)
    is_room_temperature: bool = BooleanField()

    annealing: Annealing = ForeignKeyField(Annealing, on_delete='RESTRICT',
                                           backref='steps')

    atmosphere: DependentBackref[StoichioElement]

    def __init__(self, timestamp: float, temperature: float | None,
                 is_room_temperature: bool, annealing: Annealing,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def is_plateau(self, previous_step: AnnealingStep) -> bool:
        both_room_temp = (self.is_room_temperature
                          and previous_step.is_room_temperature)
        if both_room_temp:
            return True
        else:
            if self.is_room_temperature or previous_step.is_room_temperature:
                return False  # Only one of the two is room temperature.
            else:
                return self.temperature == previous_step.temperature

    @classmethod
    def get_figure(cls, steps: list[AnnealingStep]) -> Figure:
        from components.forms.new_film_modif.fields import (PhaseDurationField,
                                                            ReachedTempField)
        timestamps = []
        time_ui_unit = PhaseDurationField.ui_unit
        for s in steps:
            quantity = ur.Quantity(s.timestamp, db_units.time)
            in_ui_unit = quantity.to(time_ui_unit).magnitude
            timestamps.append(in_ui_unit)

        temperatures = []
        temp_ui_unit = ReachedTempField.ui_unit
        for s in steps:
            if s.is_room_temperature:
                quantity = ur.Quantity(ROOM_TEMPERATURE_CELSIUS, ur.celsius)
            else:
                quantity = ur.Quantity(s.temperature, db_units.temperature)
            in_ui_unit = quantity.to(temp_ui_unit).magnitude
            temperatures.append(in_ui_unit)

        x_label = f'Time ({time_ui_unit:~P})'
        y_label = f'Temperature ({temp_ui_unit:~P})'

        df = DataFrame(zip(timestamps, temperatures),
                       columns=[x_label, y_label])

        return px.line(data_frame=df, x=x_label, y=y_label, markers=True)

    @property
    def temp_quantity(self) -> Quantity:
        if self.is_room_temperature:
            room_temp = ur.Quantity(ROOM_TEMPERATURE_CELSIUS, ur.celsius)
            return room_temp.to(db_units.temperature)
        else:
            return ur.Quantity(self.temperature, db_units.temperature)


class Etching(_BaseModel):
    has_a_pattern = BooleanField()
    film_modif = ForeignKeyField(FilmModification, on_delete='RESTRICT',
                                 backref='etchings')

    ion_etchings: DependentBackref[IonBeamEtching]
    wet_etchings: DependentBackref[WetEtching]
    lift_offs: DependentBackref[LiftOffEtching]

    patterns: DependentBackref[EtchingPattern]
    recipes: DependentBackref[EtchingRecipe]

    def __init__(self, has_a_pattern: bool, film_modif: FilmModification,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def store_related_files(self):
        if self.patterns:
            if self.patterns[0].file_bytes:
                self.patterns[0].save_bytes()
        if self.recipes:
            if self.recipes[0].file_bytes:
                self.recipes[0].save_bytes()

    def delete_related_files(self):
        if self.patterns:
            self.patterns[0].delete_file()
        if self.recipes:
            self.recipes[0].delete_file()


class IonBeamEtching(_BaseModel):
    duration = FloatField(null=True)
    flow = FloatField(null=True)
    incidence_angle = FloatField(null=True)
    rotation = FloatField(null=True)
    power = FloatField(null=True)
    pressure = FloatField(null=True)

    etching: Etching = ForeignKeyField(Etching, on_delete='RESTRICT',
                                       backref='ion_etchings')

    constituents: DependentBackref[PlasmaConstituent]

    def __init__(self, duration: float | None, flow: float | None,
                 incidence_angle: float | None, rotation: float | None,
                 power: float | None, pressure: float | None,
                 etching: Etching | None, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def to_mixture_constituents(self) -> list[MixtureConstituent]:
        return [
            MixtureConstituent(proportion=c.proportion, stoichio=c.stoichio_str)
            for c in self.constituents
        ]


class EtchingPattern(UserUploadedFile):
    etching = ForeignKeyField(Etching, backref='patterns')

    def __init__(self, label: str, file_name: str, upload_date: datetime,
                 etching: Etching, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class PlasmaConstituent(_BaseModel):
    proportion: float = FloatField()

    ion_etching: IonBeamEtching = ForeignKeyField(
        IonBeamEtching, on_delete='RESTRICT', backref='constituents')

    nominal_stoichio: DependentBackref[StoichioElement]

    def __init__(self, proportion: float, ion_etching: IonBeamEtching,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @property
    def stoichio_str(self):
        return StoichioElement.to_str(self.nominal_stoichio)

    @classmethod
    def from_stoichio(cls, stoichio: str, proportion: float,
                      etching: IonBeamEtching) -> PlasmaConstituent:
        assert 0 < proportion <= 1
        constituent = cls(
            proportion=proportion,
            ion_etching=etching,
        )
        stoichio = StoichioElement.from_str(
            stoichio,
            StoichioElement.plasma_constituent,
            constituent,
        )
        constituent.nominal_stoichio = stoichio
        return constituent


class LiftOffEtching(_BaseModel):
    used_ultrasound = BooleanField(null=True)
    ultrasound_config = CharField(null=True)

    etching: Etching = ForeignKeyField(
        Etching, on_delete='RESTRICT', backref='lift_offs')

    def __init__(self, used_ultrasound: bool | None,
                 ultrasound_config: str | None,
                 etching: Etching, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class WetEtching(_BaseModel):
    hard_bake_temperature = FloatField(null=True)
    duration = FloatField(null=True)
    used_ultrasound = BooleanField(null=True)
    ultrasound_config = CharField(null=True)
    acid_etching_depth_speed = FloatField(null=True)
    acid_etching_lateral_speed = FloatField(null=True)

    etching: Etching = ForeignKeyField(
        Etching, on_delete='RESTRICT', backref='wet_etchings')

    constituents: DependentBackref[AcidConstituent]

    def __init__(self,
                 hard_bake_temperature: float | None,
                 duration: float | None,
                 used_ultrasound: bool | None,
                 ultrasound_config: str | None,
                 acid_etching_depth_speed: float | None,
                 acid_etching_lateral_speed: float | None,
                 etching: Etching,
                 *args, **kwargs
                 ):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def to_mixture_constituents(self) -> list[MixtureConstituent]:
        return [
            MixtureConstituent(proportion=c.proportion, stoichio=c.stoichio_str)
            for c in self.constituents
        ]


class EtchingRecipe(UserUploadedFile):
    etching = ForeignKeyField(Etching, backref='recipes')

    def __init__(self, label: str, file_name: str, upload_date: datetime,
                 etching: Etching, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class AcidConstituent(_BaseModel):
    proportion: float = FloatField()

    wet_etching: WetEtching = ForeignKeyField(WetEtching, on_delete='RESTRICT',
                                              backref='constituents')

    nominal_stoichio: DependentBackref[StoichioElement]

    def __init__(self, proportion: float, wet_etching: WetEtching, *args,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @property
    def stoichio_str(self):
        return StoichioElement.to_str(self.nominal_stoichio)

    @classmethod
    def from_stoichio(cls, stoichio: str, proportion: float,
                      etching: WetEtching) -> AcidConstituent:
        assert 0 < proportion <= 1
        constituent = cls(
            proportion=proportion,
            wet_etching=etching,
        )
        stoichio = StoichioElement.from_str(
            stoichio,
            StoichioElement.acid_constituent,
            constituent,
        )
        constituent.nominal_stoichio = stoichio
        return constituent


class DeteriorationState(_BaseModel):
    date = DateField()
    made_by_email = CharField()
    length_per_px = FloatField(null=True)
    photo_file_name = CharField(null=True)
    # TODO Relevant for triode only, should we fill it in the triode form? :
    calibration_factor_comment = CharField(null=True)
    comment = CharField(null=True)
    pixel_coordinate_system: PixelCoordinateSystem = CharField(null=True)

    target: Target = ForeignKeyField(
        Target, on_delete='RESTRICT', backref='states')

    patches: DependentBackref[Patch]

    def __init__(self, date: datetime, length_per_px: float | None,
                 photo_file_name: str | None,
                 calibration_factor_comment: float | None, comment: str | None,
                 pixel_coordinate_system: PixelCoordinateSystem | None,
                 target: Target, made_by_email: str,
                 *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def photo_path(self):
        return FILE_STORAGE_PATH / self.photo_file_name

    def libraries(self) -> set[Library]:
        uses = (
            TargetUse
            .select()
            .where(TargetUse.target == self.target)
        )
        libs = set()
        for use in uses:
            use: TargetUse
            lib = use.film_layer.film.library
            libs.add(lib)
        return libs

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

    deterioration_state: DeteriorationState = ForeignKeyField(
        DeteriorationState, on_delete='RESTRICT', backref='patches')

    stoichio: DependentBackref[StoichioElement]
    vertices: DependentBackref[Vertex]

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

    def stoichio_str(self):
        return StoichioElement.to_str(self.stoichio)

    @staticmethod
    def rgb_color(stoichio_str: str) -> tuple[int, int, int]:
        rng = Random(stoichio_str)
        r = rng.randrange(0, 255)
        g = rng.randrange(0, 255)
        b = rng.randrange(0, 255)
        return r, g, b

    def plotly_color(self, stoichio_str: str = None):
        if stoichio_str is None:
            stoichio_str = StoichioElement.to_str(self.stoichio)
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
        stoichio_str = StoichioElement.to_str(self.stoichio)

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

    patch: Patch = ForeignKeyField(
        Patch, on_delete='RESTRICT', backref='vertices')

    def __init__(self, pixel_x: float, pixel_y: float, clockwise_rank: int,
                 patch: Patch, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def __str__(self):
        return f'({self.pixel_x:g}, {self.pixel_y:g})'

    def __iter__(self):
        return iter([self.pixel_x, self.pixel_y])


class TargetUse(_BaseModel):
    target: Target = ForeignKeyField(Target, backref='uses')
    film_layer: FilmLayer = ForeignKeyField(FilmLayer, on_delete='RESTRICT',
                                            backref='target_uses')

    def __init__(self, target: Target, film_layer: FilmLayer, *args, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class StoichioElement(_BaseModel):
    """Can be the stoichiometry of either of these foreign keys."""
    quantity = FloatField()
    position_in_str = IntegerField()
    element: ChemicalElement = CharField()

    substrate_layer: SubstrateLayer | ForeignKeyField = ForeignKeyField(
        SubstrateLayer, null=True, on_delete='RESTRICT',
        backref='stoichio')
    patch: Patch | ForeignKeyField = ForeignKeyField(
        Patch, null=True, on_delete='RESTRICT',
        backref='stoichio')
    film_layer: FilmLayer | ForeignKeyField = ForeignKeyField(
        FilmLayer, null=True, on_delete='RESTRICT',
        backref='nominal_stoichio')
    annealing_step: AnnealingStep | ForeignKeyField = ForeignKeyField(
        AnnealingStep, null=True, on_delete='RESTRICT',
        backref='atmosphere')
    acid_constituent: AcidConstituent | ForeignKeyField = ForeignKeyField(
        AcidConstituent, null=True, on_delete='RESTRICT',
        backref='nominal_stoichio')
    plasma_constituent: PlasmaConstituent | ForeignKeyField = ForeignKeyField(
        PlasmaConstituent, on_delete='RESTRICT', null=True,
        backref='nominal_stoichio')

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
        if self.quantity > 1:  # noqa
            return f'{self.element}{self.quantity:g}'
        else:
            return f'{self.element}'

    @staticmethod
    def to_str(elements: list[StoichioElement]) -> str:
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
