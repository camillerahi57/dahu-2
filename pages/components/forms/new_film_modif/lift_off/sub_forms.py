import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.fields import UsedUltrasoundField, \
    UltrasoundConfigField
from components.forms.new_film_modif.shared import EtchingForm
from logic.db_enums import FilmModifType
from logic.lab_modelization.db_models import LiftOffEtching, FilmModification, \
    Etching


class LiftOffForm(Form):
    def __init__(self, default_lift_off: LiftOffEtching=None):
        used_ultrasound_fld = UsedUltrasoundField(
            form_default=None,
            db_default=default_lift_off.used_ultrasound
            if default_lift_off else None,
        )
        ultrasound_config_fld = UltrasoundConfigField(
            form_default='',
            db_default=default_lift_off.ultrasound_config
            if default_lift_off else None,
        )

        default_etch = default_lift_off.etching if default_lift_off else None
        base_info_form = EtchingForm(default_etch)

        self.used_ultrasound = (used_ultrasound_fld.value
                                == UsedUltrasoundField.Option.YES)
        self.ultrasound_config = ultrasound_config_fld.value
        self.base_info_form = base_info_form

        super().__init__(fields=[used_ultrasound_fld, ultrasound_config_fld],
                         sub_forms=[base_info_form])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def to_lift_off_etching(self, film_modif: FilmModification) -> Etching:
        if not self.is_valid:
            raise PausePageRun

        etching = self.base_info_form.to_etching(film_modif)

        lift_off = LiftOffEtching(
            used_ultrasound=self.used_ultrasound,
            ultrasound_config=self.ultrasound_config,
            etching=etching,
        )

        etching.lift_offs = [lift_off]

        return etching