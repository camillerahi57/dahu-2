from datetime import datetime

import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_library.fields import (
    LibLabelField, CommentField, FilmLabelField, MadeOnField,
    MadeByField, SubstrateField, DepositTempField, NominalThicknessField,
    ShadowMaskField, NominalStoichioField, FilmLayerFunctionField,
    SputteringSystemField, DepositDistanceField, DepositAngleField,
    DepositPowerField, DepositDurationField, MagnetronModelField,
    MagnetronGeneratorField, HasActiveCoolingField, RotationSpeedField,
    FilamentCurrentStartField, FilamentCurrentEndField, AnodeCurrentField,
    AnodeVoltageField, CathodeCurrentField, CathodeVoltageField,
    DepositRateField, ArgonFlowField, NitrogenFlowField, PressureField,
    PresputteringThicknessField, LayerCountField, TargetCountField, TargetField,
    TargetChoiceField, ConfirmOrderField, IsCoSputteringField,
)
from logic.global_variables import sess, cookies
from logic.constants import SessionKeys as Sk, CookieKeys as Ck
from logic.lab_modelization.db_enums import SputteringSystem
from logic.lab_modelization.db_models import Library, Film, FilmLayer, \
    MagnetronSputtering, TriodeSputtering, Substrate, Target, TargetUse, \
    StoichioElement


class BaseInfoForm(Form):
    def __init__(self, default_lib: Library | None):
        no_db_default = default_lib is None
        st.title('New Library')
        st.divider()
        lib_label_fld = LibLabelField(
            form_default='',
            db_default=None if no_db_default
            else default_lib.label
        )
        comment_fld = CommentField(
            form_default='',
            db_default=None if no_db_default
            else default_lib.comment
        )

        self.label = lib_label_fld.value
        self.comment = comment_fld.value

        super().__init__(fields=[lib_label_fld, comment_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def to_library(self, is_archived: bool, id_: int = None) -> Library:
        if not self.is_valid:
            raise PausePageRun

        lib = Library(
            label=self.label,
            last_inspected_at=datetime.now(),
            comment=self.comment,
            hdf5_file_name=None,
            is_archived=is_archived,
        )
        if id_ is not None:
            lib.id = id_
        return lib


class FilmInfoForm(Form):
    def __init__(self, default_film: Film | None):
        with st.container(horizontal=True, vertical_alignment='center'):
            label_fld = FilmLabelField(
                form_default='',
                db_default=default_film.label
                    if default_film else None,
            )
            made_on_fld = MadeOnField(
                form_default=None,
                db_default=default_film.made_on
                    if default_film else None,
            )
            email_fld = MadeByField(
                form_default=cookies.get(Ck.LAST_EMAIL_USED),
                db_default=default_film.made_by_email
                    if default_film else None,
            )
            substrate_fld = SubstrateField(
                form_default=None,
                db_default=default_film.substrate.label
                    if default_film else None,
            )

        self.label = label_fld.value
        self.made_on = made_on_fld.value
        self.email = email_fld.value
        self.substrate_name = substrate_fld.value

        super().__init__(
            fields=[label_fld, made_on_fld, email_fld, substrate_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def add_to_library(self, library: Library):
        film = self.to_film(library)
        library.films = [film]

    def to_film(self, library: Library, id_: int = None) -> Film:
        if not self.is_valid:
            raise PausePageRun
        film = Film(
            label=self.label,
            made_on=self.made_on,
            made_by_email=self.email,
            substrate=Substrate.from_label(self.substrate_name),
            library=library,
        )
        if id_ is not None:
            film.id = id_

        return film


class LayerIntroForm(Form):
    def __init__(self, default_layer: FilmLayer | None, key: str):
        no_db_default = default_layer is None
        if default_layer:
            db_default_target_labels = [use.target.label
                                        for use in default_layer.target_uses]
            if len(db_default_target_labels) > 2:
                raise NotImplementedError(
                    "It is possible to have more than two targets in "
                    "co-sputtering in the database, but it's not implemented "
                    "in the user interface.")
        else:
            db_default_target_labels = []
        with st.container(horizontal=True):
            deposit_temp_fld = DepositTempField(
                key=f'deposit_temp_{key}',
                form_default=None,
                db_default=None if no_db_default
                else default_layer.deposit_temp
            )
            nominal_thickness_fld = NominalThicknessField(
                key=f'thickness_{key}',
                form_default=None,
                db_default=None if no_db_default
                else default_layer.nominal_thickness
            )
            shadow_mask_fld = ShadowMaskField(
                key=f'shadow_mask_{key}',
                form_default='',
                db_default=None if no_db_default
                else default_layer.shadow_mask_description
            )
            nominal_stoichio_fld = NominalStoichioField(
                key=f'stoichio_{key}',
                form_default='',
                db_default=None if no_db_default
                else default_layer.nominal_stoichio_str
            )
            layer_function_fld = FilmLayerFunctionField(
                key=f'function_{key}',
                form_default=None,
                db_default=None if no_db_default
                else default_layer.function
            )
            is_cosputter_fld = IsCoSputteringField(
                key=key,
                form_default=False,
                db_default=len(db_default_target_labels) == 2
            )
            target_label_fld = TargetChoiceField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else db_default_target_labels[0]
            )
            if is_cosputter_fld.value:
                if no_db_default or len(db_default_target_labels) < 2:
                    db_co_sputter_target = None
                else:
                    db_co_sputter_target = db_default_target_labels[1]
                target_2_label_fld = TargetChoiceField(
                    key=f'co_sputter_target_{key}',
                    form_default=None,
                    db_default=db_co_sputter_target
                )
                target_2_label = target_2_label_fld.value
            else:
                target_2_label_fld = None
                target_2_label = None
            sputtering_system_fld = SputteringSystemField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.sputtering_system
            )

        self.deposit_temp = deposit_temp_fld.in_db_unit
        self.nominal_thickness = nominal_thickness_fld.in_db_unit
        self.shadow_mask_descr = shadow_mask_fld.value
        self.nominal_stoichio = nominal_stoichio_fld.value
        self.layer_function = layer_function_fld.value
        self.sputtering_system = sputtering_system_fld.value
        self.target_label = target_label_fld.value
        self.target_2_label = target_2_label

        super().__init__(
            fields=[deposit_temp_fld, nominal_stoichio_fld, shadow_mask_fld,
                    nominal_stoichio_fld, layer_function_fld, is_cosputter_fld,
                    sputtering_system_fld, target_2_label_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''


class MagnetronForm(Form):
    def __init__(self, default_layer: MagnetronSputtering | None, key: str):
        no_db_default = default_layer is None
        with st.container(horizontal=True):
            deposit_distance_fld = DepositDistanceField(
                key=key,
                form_default=100.,
                db_default=None if no_db_default
                else default_layer.deposit_distance
            )
            deposit_angle_fld = DepositAngleField(
                key=key,
                form_default=0.,
                db_default=None if no_db_default
                else default_layer.deposit_angle
            )
            deposit_power_fld = DepositPowerField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.deposit_power
            )
            deposit_duration_fld = DepositDurationField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.deposit_duration
            )
            machine_model_fld = MagnetronModelField(
                key=key,
                form_default='',
                db_default=None if no_db_default
                else default_layer.machine_model
            )
            generator_fld = MagnetronGeneratorField(
                key=key,
                form_default='',
                db_default=None if no_db_default
                else default_layer.generator
            )

        self.deposit_distance = deposit_distance_fld.in_db_unit
        self.deposit_angle = deposit_angle_fld.in_db_unit
        self.deposit_power = deposit_power_fld.in_db_unit
        self.deposit_duration = deposit_duration_fld.in_db_unit
        self.generator = generator_fld.value
        self.machine_model = machine_model_fld.value

        super().__init__(
            fields=[deposit_distance_fld, deposit_angle_fld, deposit_power_fld,
                    deposit_duration_fld, machine_model_fld, generator_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def add_to_layer(self, layer: FilmLayer):
        if not self.is_valid:
            raise PausePageRun
        magnetron = MagnetronSputtering(
            deposit_distance=self.deposit_distance,
            deposit_angle=self.deposit_angle,
            deposit_power=self.deposit_power,
            deposit_duration=self.deposit_duration,
            generator=self.generator,
            machine_model=self.machine_model,
            film_layer=layer,
        )
        layer.magnetron_sputterings = [magnetron]


class TriodeForm(Form):
    def __init__(self, default_layer: TriodeSputtering | None, key: str):
        no_db_default = default_layer is None
        with st.container(horizontal=True, vertical_alignment='center'):
            active_cooling_fld = HasActiveCoolingField(
                key=key,
                form_default=True,
                db_default=None if no_db_default
                else default_layer.has_active_cooling
            )
            rot_speed_fld = RotationSpeedField(
                key=key,
                form_default=0.,
                db_default=None if no_db_default
                else default_layer.rotation_speed
            )
            filament_current_start_fld = FilamentCurrentStartField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.filament_current_start
            )
            filament_current_end_fld = FilamentCurrentEndField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.filament_current_end

            )
            anode_current_fld = AnodeCurrentField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.anode_current
            )
            anode_voltage_fld = AnodeVoltageField(
                key=key,
                form_default=80.,
                db_default=None if no_db_default
                else default_layer.anode_voltage
            )
            cathode_current_fld = CathodeCurrentField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.cathode_current
            )
            cathode_voltage_fld = CathodeVoltageField(
                key=key,
                form_default=900.,
                db_default=None if no_db_default
                else default_layer.cathode_voltage
            )
            deposit_rate_fld = DepositRateField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.deposit_rate
            )
            argon_flow_fld = ArgonFlowField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.argon_flow
            )
            nitrogen_flow_fld = NitrogenFlowField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.nitrogen_flow
            )
            pressure_fld = PressureField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.pressure
            )
            deposit_duration_fld = DepositDurationField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.deposit_duration
            )
            presputtering_thickness_fld = PresputteringThicknessField(
                key=key,
                form_default=None,
                db_default=None if no_db_default
                else default_layer.presputtering_thickness
            )

        self.active_cooling = active_cooling_fld.value
        self.rotation_speed = rot_speed_fld.in_db_unit
        self.filament_current_start = filament_current_start_fld.in_db_unit
        self.filament_current_end = filament_current_end_fld.in_db_unit
        self.anode_current = anode_current_fld.in_db_unit
        self.anode_voltage = anode_voltage_fld.in_db_unit
        self.cathode_current = cathode_current_fld.in_db_unit
        self.cathode_voltage = cathode_voltage_fld.in_db_unit
        self.deposit_rate = deposit_rate_fld.in_db_unit
        self.argon_flow = argon_flow_fld.in_db_unit
        self.nitrogen_flow = nitrogen_flow_fld.in_db_unit
        self.pressure = pressure_fld.in_db_unit
        self.deposit_duration = deposit_duration_fld.in_db_unit
        self.presputter_thickness = presputtering_thickness_fld.in_db_unit

        super().__init__(
            fields=[
                active_cooling_fld, rot_speed_fld, filament_current_start_fld,
                filament_current_end_fld, anode_current_fld, anode_voltage_fld,
                cathode_current_fld, cathode_voltage_fld, deposit_rate_fld,
                argon_flow_fld, nitrogen_flow_fld, pressure_fld,
                deposit_duration_fld, presputtering_thickness_fld,
            ],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def add_to_layer(self, layer: FilmLayer):
        if not self.is_valid:
            raise PausePageRun
        triode = TriodeSputtering(
            has_active_cooling=self.active_cooling,
            rotation_speed=self.rotation_speed,
            filament_current_start=self.filament_current_start,
            filament_current_end=self.filament_current_end,
            anode_current=self.anode_current,
            anode_voltage=self.anode_voltage,
            cathode_current=self.cathode_current,
            cathode_voltage=self.cathode_voltage,
            deposit_rate=self.deposit_rate,
            argon_flow=self.argon_flow,
            nitrogen_flow=self.nitrogen_flow,
            pressure=self.pressure,
            deposit_duration=self.deposit_duration,
            presputtering_thickness=self.presputter_thickness,
            film_layer=layer,
        )
        layer.triode_sputterings = [triode]


class LayerForm(Form):
    def __init__(self, default_layer: FilmLayer | None, key: str):
        with st.container(border=True):
            st.header(f"• Layer  {int(key) + 1}")
            layer_intro_form = LayerIntroForm(default_layer, key)
            sputter_system = layer_intro_form.sputtering_system
            if sputter_system == SputteringSystem.TRIODE:
                if default_layer:
                    triode_sput = default_layer.triode_sputterings[0]
                else:
                    triode_sput = None
                sputter_form = TriodeForm(triode_sput, key=key)

            elif sputter_system == SputteringSystem.MAGNETRON:
                if default_layer:
                    magnetron_sput = (default_layer.magnetron_sputterings[0])
                else:
                    magnetron_sput = None
                sputter_form = MagnetronForm(magnetron_sput, key=key)

            else:
                sputter_form = None

        self.sputter_system = layer_intro_form.sputtering_system
        self.intro_form = layer_intro_form
        self.sputter_form = sputter_form

        super().__init__(
            fields=[], sub_forms=[layer_intro_form, sputter_form]
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def to_layer(self, film: Film, position_from_buffer: int):
        if not self.is_valid:
            raise PausePageRun
        base_info = self.intro_form
        layer = FilmLayer(
            position_from_buffer=position_from_buffer,
            deposit_temp=base_info.deposit_temp,
            nominal_thickness=base_info.nominal_thickness,
            shadow_mask_description=base_info.shadow_mask_descr,
            function=base_info.layer_function,
            sputtering_system=self.sputter_system,
            film=film,
        )
        stoichio = StoichioElement.from_str(
            base_info.nominal_stoichio,
            fk_field=StoichioElement.film_layer,
            parent=layer,
        )
        layer.nominal_stoichio = stoichio
        self.sputter_form.add_to_layer(layer)

        first_target = Target.from_label(base_info.target_label)
        targets = [first_target]
        if base_info.target_2_label is not None:
            co_sputter_target = Target.from_label(base_info.target_2_label)
            targets.append(co_sputter_target)
        target_uses = [TargetUse(target=target, film_layer=layer)
                       for target in targets]
        layer.target_uses = target_uses
        return layer


class LayerListForm(Form):
    def __init__(self, default_film: Film | None):
        no_db_default = default_film is None
        layer_count_fld = LayerCountField(
            form_default=0,
            db_default=None if no_db_default
            else len(default_film.layers)
        )
        if not layer_count_fld.is_valid:
            raise PausePageRun

        layer_forms: list[LayerForm] = []
        for i in range(layer_count_fld.value):
            try:
                default_layer = default_film.layers[i]
            except IndexError, AttributeError:
                default_layer = None
            form = LayerForm(default_layer=default_layer, key=f'{i}')
            layer_forms.append(form)

        self.layer_forms = layer_forms

        super().__init__(fields=[layer_count_fld], sub_forms=layer_forms)

    def _is_coherent(self) -> tuple[bool, str]:
        if None in self.sub_forms:
            return False, "Please fill all layers."
        return True, ''

    def to_layers(self, film: Film):
        if not self.is_valid:
            raise PausePageRun
        layers = [f.to_layer(film, idx)
                  for idx, f in enumerate(self.layer_forms)]
        return layers


class TargetListForm(Form):
    def __init__(self, default_film: Film | None):
        if default_film is None:
            db_default_target_labels = []
        else:
            db_default_target_labels = default_film.target_labels
        with st.container(border=True):
            st.subheader("Targets")
            with st.container(horizontal=True):
                target_count_fld = TargetCountField(
                    form_default=0,
                    db_default=None if default_film is None
                    else len(db_default_target_labels)
                )
                if not target_count_fld.is_valid:
                    raise PausePageRun

                target_flds: list[TargetField] = []

                for i in range(target_count_fld.value):
                    try:
                        default_name = db_default_target_labels[i]
                    except IndexError:
                        default_name = None
                    field = TargetField(form_default=default_name, key=i)
                    target_flds.append(field)

        self.target_flds = target_flds

        sess[Sk.SELECTED_TARGETS] = [f.value for f in self.target_flds]

        super().__init__(fields=[target_count_fld] + target_flds,
                         sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''


class RootForm(Form):
    def __init__(self, default_lib: Library | None = None):
        default_film = default_lib.films[0] if default_lib else None

        base_info_form = BaseInfoForm(default_lib)
        film_info_form = FilmInfoForm(default_film)
        target_list_form = TargetListForm(default_film)
        st.divider()
        layer_list_form = LayerListForm(default_film)
        confirm_order_fld = ConfirmOrderField(form_default=False)

        library = base_info_form.to_library(
            is_archived=default_lib.is_archived if default_lib else False,
        )
        film_info_form.add_to_library(library)

        layers = layer_list_form.to_layers(library.films[0])
        library.films[0].layers = layers

        self.library = library

        super().__init__(
            fields=[confirm_order_fld],
            sub_forms=[base_info_form, film_info_form, layer_list_form,
                       target_list_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''
