import inspect
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from random import Random
from time import sleep
from typing import Self, Iterable, Any, cast

import chemparse
import h5py
import plotly.graph_objects as go
import streamlit as st
from pandas import DataFrame
from peewee import (
    CharField, DateTimeField, ForeignKeyField, FloatField, IntegerField,
    BooleanField, DateField, TextField, Check, DoesNotExist)
from pint.registry import Quantity
from plotly import express as px
from plotly.graph_objs import Scatter, Figure
from pyparsing import alphanums

from dahu_2_config import DOMAIN, PROBLEM_CHECK_INTERVAL, APP_VERSION
from logic.constants import (ROOM_TEMPERATURE_CELSIUS, IdType,
                             USER_DATA_PATH, CookieKeys as Ck)
from logic.lab_modelization.base_classes import _BaseModel, \
    DependentBackref, Event
from logic.lab_modelization.db_enums import (
    SputteringSystem, FilmLayerFunction,
    MagnetronSputteringGenerator as MSGenerator,
    FilmModifType, Furnace, MagnetronMachineModel as MMModel,
    PixelCoordinateSystem,
    ChemicalElement, LogSeverity, EventType, IbeMachine, CharacType, XLine,
)
from logic.lab_modelization.other_classes import MixtureConstituent
from logic.math_tools import VertexList
from logic.page_list import pages
from logic.units import ur, db_units, db_units_explanation, to_db_magnitude


# FIELD TYPES:
# https://docs.peewee-orm.com/en/latest/peewee/models.html#fields

# The 'foreign_keys': 1 is required to enforce foreign key constraints.

class Substrate(_BaseModel):
    label = CharField(unique=True)
    comment = CharField(null=True)

    layers: DependentBackref[SubstrateLayer]
    # layers: DependentBackref[SubstrateLayer]

    log_db_write = True

    def __init__(self, *args, label: str | None = None,
                 comment: str | None = None, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for l in self.layers:
            l.delete_with_parts()

    @classmethod
    def already_taken_names(cls):
        names = sorted({s.label for s in Substrate.select()},
                       key=lambda label: label)
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
    def from_label(cls, label: str) -> Substrate:
        return Substrate.get(Substrate.label == label)


class SubstrateLayer(_BaseModel):
    thickness = FloatField(null=True)
    h: IntegerField|None = IntegerField(null=True)
    k: IntegerField|None = IntegerField(null=True)
    l: IntegerField|None = IntegerField(null=True)
    position_from_back = IntegerField()
    substrate: Substrate = cast(Any, ForeignKeyField(
        Substrate, on_delete='RESTRICT', backref='layers'))

    stoichio: DependentBackref[StoichioElement]

    def __init__(self, *args,
                 thickness: float | None = None,
                 h: int | None = None,
                 k: int | None = None,
                 l: int | None = None,
                 substrate: Substrate | None = None,
                 position_from_back: int | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for s in self.stoichio:
            s.delete_with_parts()

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
    label = CharField(unique=True)
    previous_version: Target | None = cast(Any, ForeignKeyField(
        'self', null=True, on_delete='SET NULL', backref='next_versions'))
    is_archived = BooleanField()

    states: DependentBackref[DeteriorationState]
    uses: DependentBackref[TargetUse]
    next_versions: DependentBackref[Target]

    log_db_write = True

    def __init__(self, *args, made_on: datetime | None = None,
                 made_by_email: str | None = None,
                 is_archived: bool | None = None,
                 label: str | None = None,
                 previous_version: Target | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for s in self.states:
            s.delete_with_parts()

    @classmethod
    def already_taken_names(cls):
        names = sorted({t.label for t in Target.select()},
                       key=lambda name: name)
        return names

    @property
    def last_state(self) -> DeteriorationState:
        return self.old_to_recent_states()[-1]

    def old_to_recent_states(self) -> list[DeteriorationState]:
        return list(DeteriorationState.select()
                    .where(DeteriorationState.target == self)
                    .order_by(DeteriorationState.date.asc()))

    @classmethod
    def from_label(cls, label: str) -> Target:
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


class MokeCoilFactor(_BaseModel):
    validity_start = DateField()
    validity_end = DateField()
    factor = FloatField()
    comment = CharField(null=True)

    log_db_write = True

    def __init__(self, *args, validity_start: datetime | None = None,
                 validity_end: datetime | None = None,
                 factor: float | None = None, comment: str | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass


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

    log_db_write = True

    def __init__(self, *args, validity_start: datetime | None = None,
                 validity_end: datetime | None = None,
                 distance: float | None = None, poni1: float | None = None,
                 poni2: float | None = None, rot1: float | None = None,
                 rot2: float | None = None,
                 rot3: float | None = None,
                 wavelength: float | None = None, comment: str | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass


class Library(_BaseModel):
    label = CharField(unique=True)
    last_inspected_at = DateTimeField()
    comment = CharField(null=True)
    is_archived = BooleanField()

    films: DependentBackref[Film]  # Should be a list of exactly 1 element.
    general_files: DependentBackref[LibraryFile]
    refs: DependentBackref[CharacReference]

    log_db_write = True

    def __init__(self, *args, label: str | None = None,
                 last_inspected_at: datetime | None = None,
                 comment: str | None = None, is_archived: bool | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for f in self.films:
            f.delete_with_parts()
        for gf in self.general_files:
            gf.delete_with_parts()
        for r in self.refs:
            r.delete_with_parts()

    def ordered_characs(self) -> list[Charac]:
        film = list(self.films)[0]
        characs = (Charac.select()
                   .where(Charac.film == film)
                   .order_by(film.made_on))
        return [char for char in characs]

    def ordered_charac_refs(self) -> list[Charac]:
        characs = [ref.charac for ref in self.refs]

        def charac_made_on(charac: Charac):
            return charac.made_on.to_timestamp()

        return sorted(characs, key=charac_made_on)

    def all_characs(self) -> list[Charac]:
        def charac_made_on(charac: Charac):
            return charac.made_on.to_timestamp()

        return sorted(self.ordered_characs() + self.ordered_charac_refs(),
                      key=charac_made_on)

    @classmethod
    def already_taken_names(cls):
        names = sorted({l.label for l in Library.select()},
                       key=lambda label: label)
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
    substrate: Substrate = cast(Any, ForeignKeyField(
        Substrate, deferrable='INITIALLY DEFERRED'))
    library: Library = cast(Any, ForeignKeyField(
        Library, on_delete='RESTRICT', backref='films'))

    layers: DependentBackref[FilmLayer]
    modifs: DependentBackref[FilmModification]

    # Will add characterization.

    def __init__(self, *args, label: str | None = None,
                 made_on: datetime | None = None,
                 made_by_email: str | None = None,
                 substrate: Substrate | None = None,
                 library: Library | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for l in self.layers:
            l.delete_with_parts()
        for m in self.modifs:
            m.delete_with_parts()

    @classmethod
    def already_taken_names(cls):
        names = sorted({f.label for f in Film.select()},
                       key=lambda label: label)
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
            return int(layer.position_from_buffer)

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
    position_from_buffer: IntegerField = IntegerField()
    deposit_temp = FloatField(null=True)
    nominal_thickness = FloatField(null=True)
    shadow_mask_description = CharField(null=True)
    function: FilmLayerFunction = cast(Any, CharField())
    sputtering_system: SputteringSystem | None = cast(Any, CharField(null=True))

    film: Film = cast(Any, ForeignKeyField(Film, on_delete='RESTRICT',
                                                  backref='layers'))

    nominal_stoichio: DependentBackref[StoichioElement]
    target_uses: DependentBackref[TargetUse]
    magnetron_sputterings: DependentBackref[MagnetronSputtering]  # List of 1.
    triode_sputterings: DependentBackref[TriodeSputtering]  # List of 1.

    def __init__(self, *args,
                 position_from_buffer: int | None = None,
                 deposit_temp: float | None = None,
                 nominal_thickness: float | None = None,
                 shadow_mask_description: str | None = None,
                 function: FilmLayerFunction | None = None,
                 sputtering_system: SputteringSystem | None = None,
                 film: Film | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for ns in self.nominal_stoichio:
            ns.delete_with_parts()
        for tu in self.target_uses:
            tu.delete_with_parts()
        for ms in self.magnetron_sputterings:
            ms.delete_with_parts()
        for ts in self.triode_sputterings:
            ts.delete_with_parts()

    @property
    def element_str(self) -> str:
        from logic.utils import remove_digits
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
            event = Event(
                EventType.MULTIPLICITY_ERROR,
                notify=True,
                severity=LogSeverity.CRITICAL,
                description=f"A single film layer has two sputtering systems, "
                            f"which makes no sense. Concerned layer: \n{self}."
            )
            AppLog.save_new(event)
        if len(mag_sputters) == 1:
            return mag_sputters[0]
        else:
            return triode_sputters[0]

    @property
    def target_labels(self) -> list[str]:
        return [u.target.label for u in self.target_uses]

    @property
    def title_db_value_input_fields(self) \
            -> list[tuple[str, float | str, type[Any]]]:
        from components.forms.new_library.fields import (
            DepositTempField, ArgonFlowField, ShadowMaskField,
            FilmLayerFunctionField, NominalStoichioField,
        )
        return [  # noqa Type warning.
            ('Deposit temp.', self.deposit_temp, DepositTempField),
            ('Nominal thickness', self.nominal_thickness, ArgonFlowField),
            ('Shadow mask', self.shadow_mask_description, ShadowMaskField),
            ('Function', self.function, FilmLayerFunctionField),
            ('Nominal stoichio.', StoichioElement.to_str(self.nominal_stoichio),
             NominalStoichioField),
        ]


class MagnetronSputtering(_BaseModel):
    deposit_distance = FloatField(null=True)
    deposit_angle = FloatField(null=True)
    deposit_power = FloatField(null=True)
    deposit_duration = FloatField(null=True)
    generator: MSGenerator | None = cast(Any, CharField(null=True))
    machine_model: MMModel | None = cast(Any, CharField(null=True))

    film_layer: FilmLayer = cast(Any, ForeignKeyField(
        FilmLayer, on_delete='RESTRICT', backref='magnetron_sputterings',
        unique=True,
    ))

    def __init__(self, *args, deposit_distance: float | None = None,
                 deposit_angle: float | None = None,
                 deposit_power: float | None = None,
                 deposit_duration: float | None = None,
                 generator: MSGenerator | None = None,
                 machine_model: MMModel | None = None,
                 film_layer: FilmLayer | None = None
                 , **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass

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

    film_layer: FilmLayer = cast(Any, ForeignKeyField(
        FilmLayer, on_delete='RESTRICT', backref='triode_sputterings',
        unique=True,
    ))

    def __init__(self, *args,
                 has_active_cooling: bool | None = None,
                 rotation_speed: float | None = None,
                 filament_current_start: float | None = None,
                 filament_current_end: float | None = None,
                 anode_current: float | None = None,
                 anode_voltage: float | None = None,
                 cathode_current: float | None = None,
                 cathode_voltage: float | None = None,
                 deposit_rate: float | None = None,
                 argon_flow: float | None = None,
                 nitrogen_flow: float | None = None,
                 pressure: float | None = None,
                 deposit_duration: float | None = None,
                 presputtering_thickness: float | None = None,
                 film_layer: FilmLayer | None = None,
                 **kwargs
                 ):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass

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
    label: str = cast(Any, CharField())
    internal_file_name: str = cast(Any, CharField(unique=True))
    original_file_name: str = cast(Any, CharField())
    upload_date = DateField()

    _file_bytes: bytes | None = None  # Not in DB.

    def __init__(self, *args, label: str | None = None,
                 internal_file_name: str | None = None,
                 original_file_name: str | None = None,
                 upload_date: datetime | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @property
    def download_file_name(self):
        class_name = self.__class__.__name__
        return f'{class_name}_{self.label}_{self.original_file_name}'

    @classmethod
    def get_problems(cls) -> Iterable[Event]:
        # Finding files that don't exist any more:
        for file in cls.select():
            file: UserUploadedFile
            if not file.get_path().is_file():
                yield Event.from_file_missing(file)

        for prob in super().get_problems():
            yield prob

    @classmethod
    def new_internal_file_name(cls, label: str, original_file_name: str):
        from logic.utils import rand_str
        return f'{cls.__name__}_{label}_{rand_str()}_{original_file_name}'

    def delete_parts(self):
        pass

    def delete_related_files(self):
        try:
            Path.unlink(self.get_path())
            sleep(.1)
        except FileNotFoundError:
            pass

    def get_path(self):
        return USER_DATA_PATH.joinpath(self.internal_file_name)

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
        file_bytes = self.file_bytes

        with open(self.get_path(), 'wb') as file:
            if file_bytes is not None and len(file_bytes):
                file.write(file_bytes)
            else:
                raise ValueError("File cannot be empty.")

    def download_bttn(self):
        file_bytes = self.file_bytes

        if file_bytes is None:
            st.write('_File missing_')
        else:
            st.download_button(
                label=self.label,
                data=file_bytes,
                file_name=self.download_file_name,
                icon=":material/download:",
            )

    @classmethod
    def label_is_taken(cls, label: str) -> bool:
        patterns = cls.select()
        labels = [p.label for p in patterns]
        return label in labels


class FilmModification(_BaseModel):
    made_on = DateField()
    modif_number: int = cast(Any, IntegerField())
    made_by_email = CharField()
    comment = CharField(null=True)
    modif_type: FilmModifType = cast(Any, CharField())

    film: Film = cast(Any, ForeignKeyField(Film, on_delete='RESTRICT',
                                                  backref='modifs'))

    annealings: DependentBackref[Annealing]
    etchings: DependentBackref[Etching]

    log_db_write = True

    def __init__(self, *args, made_on: datetime | None = None,
                 modif_number: int | None = None,
                 made_by_email: str | None = None,
                 comment: str | None = None,
                 modif_type: FilmModifType | None = None,
                 film: Film | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for a in self.annealings:
            a.delete_with_parts()
        for e in self.etchings:
            e.delete_with_parts()

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
                        delete_nullable: bool = False,
                        *args, **kwargs):
        """Saves a film modification with its modif_number, and adds 1 to all
        modif_number attributes of subsequent film modifications."""
        for modif in FilmModification.select():
            if modif.modif_number >= self.modif_number:
                modif.modif_number -= 1
                modif.save(shift_subsequent_modifs=False)

        super().delete_instance(recursive, delete_nullable, *args, **kwargs)

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
    def previous_modif(self) -> FilmModification|None:
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
    furnace: Furnace | None = cast(Any, CharField(null=True))
    film_modif: FilmModification = cast(Any, ForeignKeyField(
        FilmModification, on_delete='RESTRICT', backref='annealings',
        unique=True,
    ))

    steps: DependentBackref[AnnealingStep]

    def __init__(self, *args, pumping_duration: float | None = None,
                 pressure: float | None = None,
                 furnace: Furnace | None = None,
                 film_modif: FilmModification | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for s in self.steps:
            s.delete_with_parts()

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

    def get_figure(self) -> Figure:
        return AnnealingStep.get_figure(self.steps)

    @property
    def title_db_value_input_fields(self):
        from components.forms.new_film_modif.fields import StartPressureField, \
            PumpingDurationField, FurnaceField
        return [
            ('Pressure', self.pressure, StartPressureField),
            ('Pumping duration', self.pumping_duration, PumpingDurationField),
            ('Furnace', self.furnace, FurnaceField),
        ]

    def phase_stoichio_strings(self):
        stoichio_strings = []
        for i_, step in enumerate(self.steps):
            if i_ == 0:
                continue  # First step has no preceding atmosphere.
            if step.preceding_was_vacuum:
                stoichio_str = 'vacuum'
            else:
                stoichio_str = StoichioElement.to_str(step.preceding_atmosphere)
            stoichio_strings.append(stoichio_str)
        return stoichio_strings


class AnnealingStep(_BaseModel):
    timestamp: float = cast(Any, FloatField())
    temperature = FloatField(null=True)
    is_room_temperature = BooleanField()
    preceding_was_vacuum: bool | None = cast(Any, BooleanField(null=True))

    annealing: Annealing = cast(Any, ForeignKeyField(
        Annealing, on_delete='RESTRICT', backref='steps'))

    preceding_atmosphere: DependentBackref[StoichioElement]

    def __init__(self, *args,
                 timestamp: float | None = None,
                 temperature: float | None = None,
                 is_room_temperature: bool | None = None,
                 preceding_was_vacuum: bool | None = None,
                 annealing: Annealing | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for se in self.preceding_atmosphere:
            se.delete_with_parts()

    def is_plateau(self, previous_step: AnnealingStep) -> bool:
        both_room_temp = (self.is_room_temperature
                          and previous_step.is_room_temperature)
        if both_room_temp:
            return True
        else:
            if self.is_room_temperature or previous_step.is_room_temperature:
                return False  # Only one of the two is room temperature.
            else:
                return bool(self.temperature == previous_step.temperature)

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


class Pattern(UserUploadedFile):
    etchings: DependentBackref[Etching]

    log_db_write = True

    def __init__(self, *args, label: str | None = None,
                 internal_file_name: str | None = None,
                 original_file_name: str | None = None,
                 upload_date: datetime | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class Recipe(UserUploadedFile):
    etchings: DependentBackref[Etching]

    log_db_write = True

    def __init__(self, *args, label: str | None = None,
                 internal_file_name: str | None = None,
                 original_file_name: str | None = None,
                 upload_date: datetime | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class Etching(_BaseModel):
    has_a_pattern = BooleanField()

    film_modif: FilmModification = cast(Any, ForeignKeyField(
        FilmModification, on_delete='RESTRICT', backref='etchings',
        unique=True))
    pattern: Pattern | None = cast(Any, ForeignKeyField(
        Pattern, backref='etchings', on_delete='RESTRICT', null=True))
    recipe: Recipe | None = cast(Any, ForeignKeyField(
        Recipe, backref='etchings', on_delete='RESTRICT', null=True))

    ion_etchings: DependentBackref[IonBeamEtching]
    wet_etchings: DependentBackref[WetEtching]
    lift_offs: DependentBackref[LiftOffEtching]

    def __init__(self, *args,
                 has_a_pattern: bool | None = None,
                 film_modif: FilmModification | None = None,
                 pattern: Pattern | None = None,
                 recipe: Recipe | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for ie in self.ion_etchings:
            ie.delete_with_parts()
        for we in self.wet_etchings:
            we.delete_with_parts()
        for lo in self.lift_offs:
            lo.delete_with_parts()


class LibraryFile(UserUploadedFile):
    library = ForeignKeyField(Library, backref='general_files')

    characs: DependentBackref[Charac]

    log_db_write = True

    def __init__(self, *args, label: str | None = None,
                 internal_file_name: str | None = None,
                 original_file_name: str | None = None,
                 upload_date: datetime | None = None,
                 library: Library | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @property
    def charac(self):
        characs = list(self.characs)
        return characs[0] if characs else None

    @property
    def is_a_charac_file(self):
        return self.charac is not None


class IonBeamEtching(_BaseModel):
    pre_etching_duration = FloatField(null=True)
    duration = FloatField(null=True)
    flow = FloatField(null=True)
    incidence_angle = FloatField(null=True)
    rotation = FloatField(null=True)
    power = FloatField(null=True)
    start_pressure = FloatField(null=True)
    target_pressure = FloatField(null=True)
    dc_grid_current = FloatField(null=True)
    machine: IbeMachine | None = cast(Any, CharField(null=True))

    etching: Etching = cast(Any, ForeignKeyField(
        Etching, on_delete='RESTRICT', backref='ion_etchings',
        unique=True,
    ))

    constituents: DependentBackref[PlasmaConstituent]

    def __init__(self, *args,
                 duration: float | None = None,
                 flow: float | None = None,
                 incidence_angle: float | None = None,
                 rotation: float | None = None,
                 power: float | None = None,
                 start_pressure: float | None = None,
                 etching: Etching | None = None,
                 target_pressure: float | None = None,
                 pre_etching_duration: float | None = None,
                 dc_grid_current: float | None = None,
                 machine: IbeMachine | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for c in self.constituents:
            c.delete_with_parts()

    def to_mixture_constituents(self) -> list[MixtureConstituent]:
        return [
            MixtureConstituent(proportion=c.proportion, stoichio=c.stoichio_str)
            for c in self.constituents
        ]

    @property
    def title_db_value_input_fields(self):
        from components.forms.new_film_modif.fields import (
            IonDurationField, FlowField, AngleField, RotationSpeedField,
            PowerField,
            StartPressureField,
        )
        return [
            ('Duration', self.duration, IonDurationField),
            ('Flow', self.flow, FlowField),
            ('Incidence angle', self.incidence_angle, AngleField),
            ('Rotation', self.rotation, RotationSpeedField),
            ('Power', self.power, PowerField),
            ('Pressure', self.start_pressure, StartPressureField),
        ]


class PlasmaConstituent(_BaseModel):
    proportion: float = cast(Any, FloatField())

    ion_etching: IonBeamEtching = cast(Any, ForeignKeyField(
        IonBeamEtching, on_delete='RESTRICT', backref='constituents'))

    nominal_stoichio: DependentBackref[StoichioElement]

    def __init__(self, *args, proportion: float | None = None,
                 ion_etching: IonBeamEtching | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for se in self.nominal_stoichio:
            se.delete_with_parts()

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
        field: ForeignKeyField = cast(Any, StoichioElement.plasma_constituent)
        stoichio = StoichioElement.from_str(
            stoichio,
            field,
            constituent,
        )
        constituent.nominal_stoichio = stoichio
        return constituent


class LiftOffEtching(_BaseModel):
    used_ultrasound = BooleanField(null=True)
    ultrasound_config = CharField(null=True)
    etching: Etching = cast(Any, ForeignKeyField(
        Etching, on_delete='RESTRICT', backref='lift_offs', unique=True,
    ))

    def __init__(self, *args, used_ultrasound: bool | None = None,
                 ultrasound_config: str | None = None,
                 etching: Etching | None = None, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass


class WetEtching(_BaseModel):
    hard_bake_temperature = FloatField(null=True)
    etching_duration = FloatField(null=True)
    development_duration = FloatField(null=True)
    used_ultrasound = BooleanField(null=True)
    ultrasound_config = CharField(null=True)
    base = CharField(null=True)
    acid = CharField(null=True)
    acid_etching_depth_speed = FloatField(null=True)
    acid_etching_lateral_speed = FloatField(null=True)

    etching: Etching = cast(Any, ForeignKeyField(
        Etching, on_delete='RESTRICT', backref='wet_etchings', unique=True))

    solvents: DependentBackref[EtchingSolvent]

    def __init__(self, *args,
                 hard_bake_temperature: float | None = None,
                 etching_duration: float | None = None,
                 development_duration: float | None = None,
                 used_ultrasound: bool | None = None,
                 ultrasound_config: str | None = None,
                 base: str | None = None,
                 acid: str | None = None,
                 acid_etching_depth_speed: float | None = None,
                 acid_etching_lateral_speed: float | None = None,
                 etching: Etching | None = None,
                 **kwargs
                 ):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for s in self.solvents:
            s.delete_with_parts()

    @property
    def title_db_value_input_fields(self):
        from components.forms.new_film_modif.fields import (
            HardBakeTempField, AcidEtchingDurationField, UsedUltrasoundField,
            UltrasoundConfigField, EtchingDepthSpeedField,
            EtchingLateralSpeedField, BaseField, AcidField, SolventField,
        )
        solvent_str = ' '.join([f'**{s.step_idx + 1}.** *{s.label}*'
                                for s in self.solvents]) + '.'
        return [
            ('Hard bake temperature', self.hard_bake_temperature,
             HardBakeTempField),
            ('Duration', self.etching_duration, AcidEtchingDurationField),
            ('Used ultrasound', self.used_ultrasound, UsedUltrasoundField),
            ('Ultrasound config', self.ultrasound_config,
             UltrasoundConfigField),
            ('Base', self.base, BaseField),
            ('Acid', self.acid, AcidField),
            ('Solvents', solvent_str, SolventField),
            ('Etching depth speed', self.acid_etching_depth_speed,
             EtchingDepthSpeedField),
            ('Etching lateral speed', self.acid_etching_lateral_speed,
             EtchingLateralSpeedField),
        ]


class EtchingSolvent(_BaseModel):
    etching: WetEtching = cast(Any, ForeignKeyField(
        WetEtching, on_delete='RESTRICT', backref='solvents'))
    label: str = cast(Any, CharField())
    step_idx: int = cast(Any, IntegerField())

    def __init__(self, *args, etching: WetEtching | None = None,
                 label: str | None = None,
                 step_idx: int | None = None, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass


class DeteriorationState(_BaseModel):
    date = DateField()
    made_by_email = CharField()
    length_per_px = FloatField(null=True)
    # TODO Relevant for triode only, should we fill it in the triode form? :
    calibration_factor_comment = CharField(null=True)
    comment = CharField(null=True)
    pixel_coordinate_system: PixelCoordinateSystem | None = cast(
        Any, CharField(null=True))

    target: Target = cast(Any, ForeignKeyField(
        Target, on_delete='RESTRICT', backref='states'))

    patches: DependentBackref[Patch]
    photos: DependentBackref[TargetPhoto]

    log_db_write = True

    def __init__(self, *args,
                 date: datetime,
                 length_per_px: float | None = None,
                 calibration_factor_comment: float | None = None,
                 comment: str | None = None,
                 pixel_coordinate_system: PixelCoordinateSystem | None = None,
                 target: Target | None = None,
                 made_by_email: str | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for p in self.patches:
            p.delete_with_parts()
        for p in self.photos:
            p.delete_with_parts()

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


class TargetPhoto(UserUploadedFile):
    target_state: DeteriorationState = cast(Any, ForeignKeyField(
        DeteriorationState, backref='photos', on_delete='RESTRICT', unique=True))

    log_db_write = True

    def __init__(self, *args, label: str | None = None,
                 internal_file_name: str | None = None,
                 original_file_name: str | None = None,
                 upload_date: datetime | None = None,
                 target_state: DeteriorationState | None = None, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)


class Patch(_BaseModel):
    stack_idx = IntegerField()

    deterioration_state: DeteriorationState = cast(Any, ForeignKeyField(
        DeteriorationState, on_delete='RESTRICT', backref='patches'))

    stoichio: DependentBackref[StoichioElement]
    vertices: DependentBackref[Vertex]

    def __init__(self, *args, stack_idx: int | None = None,
                 deterioration_state: DeteriorationState | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def __str__(self):
        return f'Patch of stoichiometry {self.stoichio}'

    def delete_parts(self):
        for se in self.stoichio:
            se.delete_with_parts()
        for v in self.vertices:
            v.delete_with_parts()

    @classmethod
    def from_polygon(cls, stoichio_str: str,
                     vertices: VertexList,
                     stack_idx: int,
                     deterioration_state: DeteriorationState) \
            -> Patch:
        patch = cls(stack_idx=stack_idx,
                    deterioration_state=deterioration_state)
        fk_field: ForeignKeyField = cast(Any, StoichioElement.patch)
        patch.stoichio = StoichioElement.from_str(
            formula=stoichio_str,
            fk_field=fk_field,
            parent=patch,
        )
        patch.vertices = [
            Vertex(pixel_x=x, pixel_y=y, clockwise_rank=i, patch=patch)
            for i, (x, y) in enumerate(vertices)
        ]
        return patch

    @staticmethod
    def is_valid_formula(stoichio_str: str) -> tuple[bool, str]:
        from logic.utils import letter_count
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

    def plotly_color(self, stoichio_str: str | None = None):
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


class Vertex(_BaseModel):
    pixel_x: float = cast(Any, FloatField())
    pixel_y: float = cast(Any, FloatField())
    clockwise_rank = IntegerField()

    patch: Patch = cast(Any, ForeignKeyField(
        Patch, on_delete='RESTRICT', backref='vertices'))

    def __init__(self, *args, pixel_x: float | None = None,
                 pixel_y: float | None = None,
                 clockwise_rank: int | None = None,
                 patch: Patch | None = None, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass

    def __str__(self):
        return f'({self.pixel_x:g}, {self.pixel_y:g})'

    def __iter__(self):
        return iter([self.pixel_x, self.pixel_y])


class TargetUse(_BaseModel):
    target: Target = cast(Any, ForeignKeyField(Target, backref='uses'))
    film_layer: FilmLayer = cast(Any, ForeignKeyField(
        FilmLayer, on_delete='RESTRICT', backref='target_uses'))

    def __init__(self, *args, target: Target | None = None,
                 film_layer: FilmLayer | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass


class StoichioElement(_BaseModel):
    """Can be the stoichiometry of either of these foreign keys."""
    quantity: float = cast(Any, FloatField())
    position_in_str = IntegerField()
    element: ChemicalElement = cast(Any, CharField())

    substrate_layer: SubstrateLayer | None = cast(Any, ForeignKeyField(
        SubstrateLayer, null=True, on_delete='RESTRICT',
        backref='stoichio'))
    patch: Patch | ForeignKeyField = ForeignKeyField(
        Patch, null=True, on_delete='RESTRICT',
        backref='stoichio')
    film_layer: FilmLayer | ForeignKeyField = ForeignKeyField(
        FilmLayer, null=True, on_delete='RESTRICT',
        backref='nominal_stoichio')
    annealing_step: AnnealingStep | ForeignKeyField = ForeignKeyField(
        AnnealingStep, null=True, on_delete='RESTRICT',
        backref='preceding_atmosphere')
    plasma_constituent: PlasmaConstituent | ForeignKeyField = ForeignKeyField(
        PlasmaConstituent, on_delete='RESTRICT', null=True,
        backref='nominal_stoichio')

    def __init__(self, *args,
                 quantity: float | None = None,
                 position_in_str: int | None = None,
                 element: ChemicalElement | None = None,
                 substrate_layer: SubstrateLayer | None = None,
                 patch: Patch | None = None,
                 film_layer: FilmLayer | None = None,
                 annealing: Annealing | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass

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


class Charac(_BaseModel):
    made_on = DateField()
    made_by_email = CharField()
    comment = TextField(null=True)
    type_: CharacType = cast(Any, CharField())

    film: Film = cast(Any, ForeignKeyField(
        Film, on_delete='RESTRICT', backref='characs'))
    last_modif: FilmModification | None = cast(Any, ForeignKeyField(
        FilmModification, null=True, on_delete='RESTRICT', backref='characs'))
    file: LibraryFile = cast(Any, ForeignKeyField(
        LibraryFile, on_delete='RESTRICT', backref='characs'))

    refs: DependentBackref[CharacReference]
    edxs: DependentBackref[Edx]

    log_db_write: bool = False

    def __init__(self, *args,
                 made_on: datetime | None = None,
                 made_by_email: str | None = None,
                 comment: str | None = None,
                 type_: CharacType | None = None,
                 film: Film | None = None,
                 last_modif: FilmModification | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for r in self.refs:
            r.delete_with_parts()
        for e in self.edxs:
            e.delete_with_parts()

    @property
    def edx(self):
        return list(self.edxs)[0]


class CharacReference(_BaseModel):
    charac: Charac = cast(Any, ForeignKeyField(
        Charac, on_delete='RESTRICT', backref='refs'))
    lib: Library = cast(Any, ForeignKeyField(
        Library, on_delete='RESTRICT', backref='refs'))

    def __init__(self, *args,
                 charac: Charac | None = None,
                 lib: Library | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass


class Edx(_BaseModel):
    electron_energy = FloatField()
    working_distance = FloatField()
    magnification = FloatField()
    acquisition_duration = FloatField()

    charac: Charac = cast(Any, ForeignKeyField(Charac,
                                                      on_delete='RESTRICT',
                                                      backref='edxs'))

    elements: DependentBackref[ChemicalElementEdx]

    def __init__(self, *args,
                 electron_energy: float | None = None,
                 working_distance: float | None = None,
                 magnification: float | None = None,
                 acquisition_duration: float | None = None,
                 charac: Charac | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        for e in self.elements:
            e.delete_with_parts()

    @property
    def electron_energy_quantity(self) -> Quantity:
        return self.electron_energy * ur.keV

    @property
    def working_distance_quantity(self) -> Quantity:
        return self.working_distance * ur.mm

    @property
    def acquisition_duration_quantity(self) -> Quantity:
        return self.acquisition_duration * ur.ms

    @staticmethod
    def get_hdf5_datasets(hdf5_file, dataset_type):
        """
        :param hdf5_file: Root group from a library high-throughput HDF5 file
        :param dataset_type:
        :return:
        """
        if dataset_type == "all":
            return list(hdf5_file.keys())

        else:
            dataset_list = []
            for dataset, dataset_group in hdf5_file.items():
                if "HT_type" in dataset_group.attrs:
                    if dataset_type in dataset_group.attrs["HT_type"]:
                        dataset_list.append(dataset)

            return dataset_list

    @classmethod
    def from_hdf5(cls, hdf5_path: Path):
        with h5py.File(hdf5_path, "r") as hdf5_file:
            dataset_list = cls.get_hdf5_datasets(hdf5_file, dataset_type="edx")
            edx_group = hdf5_file[dataset_list[0]]
            positions_group = edx_group['positions']
            ref_instrument_group = positions_group[
                f"{positions_group.keys[0]}/instrument"]

            prim_energy_path = "/ESMAHeader/PrimaryEnergy"
            primary_energy_float = ref_instrument_group[prim_energy_path][()]
            primary_energy = to_db_magnitude(primary_energy_float * ur.keV)

            work_dist_path = "/ESMAHeader/WorkingDistance"
            working_distance_float = ref_instrument_group[work_dist_path][()]
            working_distance = to_db_magnitude(working_distance_float * ur.mm)

            magnification_path = "/ESMAHeader/Magnification"
            magnification = ref_instrument_group[magnification_path][()]

            hardware_path = "/SpectrumHardwareHeader/RealTime"
            acquisition_time_float = ref_instrument_group[hardware_path][()]
            acquisition_time = to_db_magnitude(acquisition_time_float * ur.ms)

            results_dict = dict()
            for position, position_group in edx_group["positions"].items:
                for element, element_group in position_group["results"].items():
                    element_symbol = element.split(" ")[1].strip()

                    if ("AtomPercent" in element_group
                            and element_symbol not in results_dict):
                        value = element_group["AtomPercent"][()]
                        results_dict[element_symbol] = {
                            "min": value,
                            "max": value,
                            "sum": value,
                            "count": 1,
                            "Xline": element_group["XLine"][()],
                            "quantified": True
                        }

                    elif ("AtomPercent" in element_group
                          and element_symbol in results_dict):
                        value = element_group["AtomPercent"][()]
                        if value < results_dict[element_symbol]["min"]:
                            results_dict[element_symbol]["min"] = value
                        if value > results_dict[element_symbol]["max"]:
                            results_dict[element_symbol]["max"] = value

                        results_dict[element_symbol]["sum"] += value
                        results_dict[element_symbol]["count"] += 1

                    elif ("AtomPercent" not in element_group
                          and element_symbol not in results_dict):
                        results_dict[element_symbol] = {
                            "min": None,
                            "max": None,
                            "sum": None,
                            "count": None,
                            "Xline": element_group["XLine"][()],
                            "quantified": False
                        }

            hdf5_file.purge()

        element_classes = ChemicalElementEdx.from_dict(results_dict)
        parsed = cls(
            electron_energy=primary_energy,
            working_distance=working_distance,
            magnification=magnification,
            acquisition_duration=acquisition_time,
            chemical_element_edx_list=element_classes,
        )

        return parsed


class ChemicalElementEdx(_BaseModel):
    element: ChemicalElement = cast(Any, CharField())
    min_atom_percent = FloatField(null=True)
    max_atom_percent = FloatField(null=True)
    mean_atom_percent = FloatField(null=True)
    quantified = BooleanField()
    x_line: XLine = cast(Any, CharField())

    edx: Edx = cast(Any, ForeignKeyField(Edx, on_delete='RESTRICT',
                                                backref='elements'))

    def __init__(self, *args,
                 element: ChemicalElement | None = None,
                 min_atom_percent: float | None = None,
                 max_atom_percent: float | None = None,
                 mean_atom_percent: float | None = None,
                 quantified: bool | None = None,
                 x_line: XLine | None = None,
                 edx: Edx | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    def delete_parts(self):
        pass

    @classmethod
    def from_dict(cls, elements: dict) -> list[Self]:
        element_list = [
            cls(
                element=element,
                min_atom_percent=data["min"],
                max_atom_percent=data["max"],
                mean_atom_percent=data["sum"] / data["count"],
                quantified=data["quantified"],
                x_line=data["Xline"],
            )
            for element, data in elements.items()
        ]
        return element_list


class AppMetadata(_BaseModel):
    """Table with only one row (class with only one instance), also called
    'a singleton'."""
    is_the_only_row = BooleanField(
        unique=True, constraints=[Check('is_the_only_row = TRUE')])
    db_units_description = TextField()
    next_backup_at = DateTimeField()
    next_problem_check_at = DateTimeField()
    current_app_version = IntegerField()

    def __init__(self, *args,
                 is_the_only_row: bool = True,
                 db_units_description: str = db_units_explanation,
                 next_backup_at: datetime | None = None,
                 next_problem_check_at: datetime | None = None,
                 current_app_version: int | None = None,
                 **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @classmethod
    def get_or_new(cls):
        try:
            return cls.get()
        except DoesNotExist:
            return cls(
                next_backup_at=datetime.now(),
                next_problem_check_at=datetime.now() + PROBLEM_CHECK_INTERVAL,
                current_app_version=APP_VERSION,
            )

    def save(self, force_insert: bool = False, only: list | None = None,
             *args, **kwargs):
        self.current_app_version = APP_VERSION
        super().save(force_insert=force_insert, only=only, *args, **kwargs)


class AppLog(_BaseModel):
    """Table with logs about various app event."""
    timestamp = DateTimeField()
    ip_address = cast(Any, CharField(null=True))
    email_in_cookies = cast(Any, CharField(null=True))
    notify = BooleanField()
    marked_read = BooleanField()
    marked_solved = BooleanField()
    severity: LogSeverity = cast(Any, CharField())
    event_type: EventType = cast(Any, CharField())
    event_description = TextField(unique=True)  # Don't log info twice.

    def __init__(self, *args, timestamp: datetime | None = None,
                 ip_address: str | None = None,
                 email_in_cookies: str | None = None,
                 notify: bool | None = None, marked_read: bool | None = None,
                 marked_solved: bool | None = None,
                 severity: LogSeverity | None = None,
                 event_type: str | None = None,
                 event_description: str | None = None, **kwargs):
        model_kwargs = self.get_model_kwargs(locals())
        super().__init__(*args, **model_kwargs, **kwargs)

    @classmethod
    def save_new(cls,
                 event: Event,
                 marked_read: bool = False,
                 marked_solved: bool = False,
                 timestamp: datetime | None = None):
        from logic.cookie_init import cookies
        new_log = cls(
            timestamp=timestamp or datetime.now(),
            ip_address=st.context.ip_address,
            email_in_cookies=cookies.get(Ck.LAST_EMAIL_USED),
            notify=event.notify,
            marked_read=marked_read,
            marked_solved=marked_solved,
            severity=event.severity,
            event_type=event.type,
            event_description=event.description,
        )
        print(new_log.event_description)
        new_log.save()

    @classmethod
    def filtered_query(cls, severities: list[LogSeverity] | None = None,
                       show_read=True, show_solved=True):
        if severities is None:
            severities = list(LogSeverity)
        query = (AppLog.select()
                 .order_by(AppLog.timestamp.desc())  # noqa Wrong warning.
                 .where(AppLog.severity.in_(severities))  # noqa Weird warning.
                 )
        if not show_read:
            query = query.where(AppLog.marked_read == False)
        if not show_solved:
            query = query.where(AppLog.marked_solved == False)

        return query

    def save(self, force_insert: bool = False, only: list | None = None,
             *args, **kwargs):
        """If the current app_log has the same description as an existing
        app_log, we skip the save process. However, we update some fields
        of the existing log, especially in order to display it as recent."""
        # Check for existing:
        similar_log_query = (
            AppLog.select()
            .where(AppLog.event_description == self.event_description)
            .where(AppLog.id != self.id)
        )
        if similar_log_query.exists():
            same_log: AppLog = similar_log_query.get()
            same_log.timestamp = self.timestamp
            same_log.ip_address = self.ip_address
            same_log.email_in_cookies = self.email_in_cookies
            same_log.notify = self.notify
            same_log.severity = self.severity
            same_log.event_type = self.event_type
            super(AppLog, same_log).save()
            return
        else:
            super().save(force_insert=force_insert, only=only, *args, **kwargs)

    @classmethod
    def unread_warning_notif_count(cls) -> int:
        return (AppLog.select()
                .where(AppLog.severity == LogSeverity.WARNING)
                .where(AppLog.marked_read == False)
                .where(AppLog.notify == True)
                .count())

    @classmethod
    def unsolved_critical_notif_count(cls) -> int:
        return (AppLog.select()
                .where(AppLog.severity == LogSeverity.CRITICAL)
                .where(AppLog.marked_solved == False)
                .where(AppLog.notify == True)
                .count())


# Don't move to another file because it looks for classes in the same file:
@dataclass
class ModelCollection:
    models: list[type[_BaseModel]]
    name_to_model: dict[str, type[_BaseModel]]

    @classmethod
    def from_current_module(cls):
        def is_a_model(class_):
            return (
                    inspect.isclass(class_)
                    and issubclass(class_, _BaseModel)
                    and not class_.__name__.startswith('_')
            )

        name_models = inspect.getmembers(sys.modules[__name__], is_a_model)
        return cls(
            models=[model for name, model in name_models],
            name_to_model={name: model for name, model in name_models},
        )

    def __iter__(self):
        return iter(self.models)


# Don't move to another file because it looks for classes in the same file:
dahu_2_models = ModelCollection.from_current_module()
