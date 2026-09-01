import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.fields import (
    IonDurationField, FlowField, AngleField, RotationSpeedField, PowerField,
    StartPressureField, TargetPressureField, PreEtchDurationField,
    DcGridCurrentField, IbeMachineField)
from components.forms.new_film_modif.shared import ConstituentListForm, \
    EtchingForm
from logic.lab_modelization.db_enums import IbeMachine
from logic.lab_modelization.db_models import IonBeamEtching, \
    FilmModification, Etching


class IonEtchingForm(Form):
    def __init__(self, default_beam_etch: IonBeamEtching|None):

        with st.container(horizontal=True):
            pre_etch_duration_fld = PreEtchDurationField(
                form_default=None,
                db_default=default_beam_etch.pre_etching_duration
                    if default_beam_etch else None,
            )
            duration_fld = IonDurationField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.duration,
            )
            angle_fld = AngleField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.incidence_angle
            )
            rotation_fld = RotationSpeedField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.rotation
            )
            power_fld = PowerField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.power
            )
            start_pressure_fld = StartPressureField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.start_pressure
            )
            target_pressure_fld = TargetPressureField(
                form_default=None,
                db_default=default_beam_etch.target_pressure
                    if default_beam_etch else None
            )
            dc_grid_current_fld = DcGridCurrentField(
                form_default=None,
                db_default=default_beam_etch.dc_grid_current
                    if default_beam_etch else None
            )
            machine_fld = IbeMachineField(
                form_default=IbeMachine.IBE_NANO_FAB,
                db_default=default_beam_etch.machine
                    if default_beam_etch else None
            )
            flow_fld = FlowField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.flow,
            )

        default_etch = default_beam_etch.etching if default_beam_etch else None
        base_info_form = EtchingForm(default_etch)

        st.divider()
        constituent_form = ConstituentListForm(
            default_constituents=default_beam_etch.to_mixture_constituents()
                if default_beam_etch else None,
            title='Plasma Constituents',
        )

        self.pre_etching_duration = pre_etch_duration_fld.in_db_unit
        self.duration = duration_fld.in_db_unit
        self.flow = flow_fld.in_db_unit
        self.incidence_angle = angle_fld.in_db_unit
        self.rotation = rotation_fld.in_db_unit
        self.power = power_fld.in_db_unit
        self.start_pressure = start_pressure_fld.in_db_unit
        self.target_pressure = target_pressure_fld.in_db_unit
        self.dc_grid_current = dc_grid_current_fld.in_db_unit
        self.machine = machine_fld.value
        self.base_info_form = base_info_form
        self.constituent_form = constituent_form
        super().__init__(
            fields=[duration_fld, flow_fld, angle_fld, rotation_fld, power_fld,
                    start_pressure_fld, target_pressure_fld, machine_fld,
                    pre_etch_duration_fld, dc_grid_current_fld],
            sub_forms=[base_info_form, constituent_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        # User can indicate that there is a pattern without providing it.
        return True, ''

    def to_ion_etching(self, film_modif: FilmModification) \
            -> Etching:
        """Return an ion etching object with pattern image bytes."""
        if not self.is_valid:
            raise PausePageRun

        etching = self.base_info_form.to_etching(film_modif)

        ion_etching = IonBeamEtching(
            pre_etching_duration=self.pre_etching_duration,
            duration=self.duration,
            flow=self.flow,
            incidence_angle=self.incidence_angle,
            rotation=self.rotation,
            power=self.power,
            start_pressure=self.start_pressure,
            target_pressure=self.target_pressure,
            etching=etching,
            dc_grid_current=self.dc_grid_current,
            machine=self.machine,
        )
        etching.ion_etchings = [ion_etching]

        constituents = self.constituent_form.to_plasma(ion_etching)
        ion_etching.constituents = constituents

        return etching