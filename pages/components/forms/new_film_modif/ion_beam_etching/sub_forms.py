import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.fields import IonDurationField, FlowField, \
    AngleField, RotationField, PowerField, PressureField
from components.forms.new_film_modif.shared import ConstituentListForm, \
    EtchingForm
from logic.lab_modelization.db_models import IonBeamEtching, \
    FilmModification, Etching


class IonEtchingForm(Form):
    def __init__(self, default_beam_etch: IonBeamEtching|None):

        with st.container(horizontal=True):
            duration_fld = IonDurationField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.duration,
            )
            flow_fld = FlowField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.flow,
            )
            angle_fld = AngleField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.incidence_angle
            )
            rotation_fld = RotationField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.rotation
            )
            power_fld = PowerField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.power
            )
            pressure_fld = PressureField(
                form_default=None,
                db_default=None if not default_beam_etch
                    else default_beam_etch.pressure
            )

        default_etch = default_beam_etch.etching if default_beam_etch else None
        base_info_form = EtchingForm(default_etch)

        st.divider()
        constituent_form = ConstituentListForm(
            default_constituents=default_beam_etch.to_mixture_constituents()
                if default_beam_etch else None,
            title='Plasma Constituents',
        )

        self.duration = duration_fld.in_db_unit
        self.flow = flow_fld.in_db_unit
        self.incidence_angle = angle_fld.in_db_unit
        self.rotation = rotation_fld.in_db_unit
        self.power = power_fld.in_db_unit
        self.pressure = pressure_fld.in_db_unit
        self.base_info_form = base_info_form
        self.constituent_form = constituent_form
        super().__init__(
            fields=[duration_fld, flow_fld, angle_fld, rotation_fld, power_fld,
                    pressure_fld],
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
            duration=self.duration,
            flow=self.flow,
            incidence_angle=self.incidence_angle,
            rotation=self.rotation,
            power=self.power,
            pressure=self.pressure,
            etching=etching
        )
        etching.ion_etchings = [ion_etching]

        constituents = self.constituent_form.to_plasma(ion_etching)
        ion_etching.constituents = constituents

        return etching