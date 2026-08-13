import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.fields import HardBakeTempField, \
    AcidEtchingDurationField, UsedUltrasoundField, \
    UltrasoundConfigField, EtchingDepthSpeedField, EtchingLateralSpeedField, \
    BaseField, AcidField, SolventField
from components.forms.new_film_modif.shared import \
    EtchingForm
from logic.lab_modelization.db_models import WetEtching, \
    Etching, FilmModification


class WetEtchingForm(Form):
    def __init__(self, default_wet_etch: WetEtching=None):
        with st.container(horizontal=True):
            bake_temp_fld = HardBakeTempField(
                form_default=None,
                db_default=default_wet_etch.hard_bake_temperature
                if default_wet_etch else None,
            )
            etching_duration_fld = AcidEtchingDurationField(
                form_default=None,
                db_default=default_wet_etch.duration
                if default_wet_etch else None,
            )
        st.divider()
        with st.container(horizontal=True):
            used_ultrasound_fld = UsedUltrasoundField(
                form_default=None,
                db_default=default_wet_etch.used_ultrasound
                if default_wet_etch else None,
            )
            ultrasound_config_fld = UltrasoundConfigField(
                form_default='',
                db_default=default_wet_etch.ultrasound_config
                if default_wet_etch else None,
            )
        st.divider()
        with st.container(horizontal=True):
            base_fld = BaseField(
                form_default=None,
                db_default=default_wet_etch.base
                    if default_wet_etch else None,
            )
            acid_fld = AcidField(
                form_default=None,
                db_default=default_wet_etch.acid
                    if default_wet_etch else None,
            )
            solvent_fld = SolventField(
                form_default=None,
                db_default=default_wet_etch.solvent
                    if default_wet_etch else None,
            )
        st.divider()
        with st.container(horizontal=True):
            depth_speed_fld = EtchingDepthSpeedField(
                form_default=None,
                db_default=default_wet_etch.acid_etching_depth_speed
                if default_wet_etch else None,
            )
            lateral_speed_fld = EtchingLateralSpeedField(
                form_default=None,
                db_default=default_wet_etch.acid_etching_lateral_speed
                if default_wet_etch else None,
            )
        st.divider()

        default_etch = default_wet_etch.etching if default_wet_etch else None
        base_info_form = EtchingForm(default_etch)

        st.divider()

        self.hard_bake_temp = bake_temp_fld.in_db_unit
        self.duration = etching_duration_fld.in_db_unit
        self.used_ultrasound = (used_ultrasound_fld.value
                                == UsedUltrasoundField.Option.YES)
        self.ultrasound_config = ultrasound_config_fld.value
        self.depth_speed = depth_speed_fld.in_db_unit
        self.lateral_speed = lateral_speed_fld.in_db_unit
        self.base = base_fld.value
        self.acid = acid_fld.value
        self.solvent = solvent_fld.value

        self.base_info_form = base_info_form
        super().__init__(
            fields=[bake_temp_fld, etching_duration_fld, used_ultrasound_fld,
                    ultrasound_config_fld, depth_speed_fld, lateral_speed_fld,
                    base_fld, acid_fld, solvent_fld],
            sub_forms=[base_info_form]
        )

    def _is_coherent(self) -> tuple[bool, str]:
        # User can indicate that there is a pattern without providing it.
        return True, ''

    def to_wet_etching(self, film_modif: FilmModification) -> Etching:
        """Return a wet etching object with pattern image bytes."""
        if not self.is_valid:
            raise PausePageRun

        etching = self.base_info_form.to_etching(film_modif)

        wet_etching = WetEtching(
            hard_bake_temperature=self.hard_bake_temp,
            duration=self.duration,
            used_ultrasound=self.used_ultrasound,
            ultrasound_config=self.ultrasound_config,
            base=self.base,
            acid=self.acid,
            solvent=self.solvent,
            acid_etching_depth_speed=self.depth_speed,
            acid_etching_lateral_speed=self.lateral_speed,
            etching=etching,
        )

        etching.wet_etchings = [wet_etching]

        return etching
