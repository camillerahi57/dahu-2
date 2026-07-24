from enum import StrEnum

import streamlit as st

from components.forms.shared2 import Field, FieldType as Ft, UnitField
from components.streamlit_tools import sess
from logic.constants import SessionKeys as Sk, CookieKeys as Ck, \
    FILM_INIT_STATE
from logic.db_enums import FilmModifType, Furnace, ChemicalElement
from logic.functions import is_valid_email_address
from logic.lab_modelization.db_models import FilmModification, Patch
from logic.units import ur


class MadeByField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):  # noqa
        if Ck.LAST_EMAIL_USED in st.session_state:
            value = st.session_state[Ck.LAST_EMAIL_USED]
        else:
            value = ''
        return st.text_input("Made by (email address)",
                             value=value, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        if not is_valid_email_address(input_):
            return False, 'Please enter a valid email address.'
        st.session_state[Ck.LAST_EMAIL_USED] = input_
        return True, ''


class MadeOnField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        return st.date_input("Made on",
                             max_value='today')

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class ModifTypeField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        options = list(FilmModifType)
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.radio('Modification type', options=FilmModifType,
                     index=index, horizontal=True)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ is None or input_ == '':
            return False, 'Please select a modification type.'
        return True, ''


class MadeAfterField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        film = sess[Sk.CURRENT_FILM]
        film_modifs = (FilmModification.select()
                       .where(FilmModification.film == film))
        def get_modif_count(fm: FilmModification):
            return fm.modif_number
        film_modifs = sorted(list(film_modifs), key=get_modif_count)
        options = [
            (modif.modif_number, modif.modif_type)
            for modif in film_modifs
        ]
        options = sorted(options, key=lambda x: x[0])
        options = [(-1, FILM_INIT_STATE)] + options
        return st.selectbox(
            'Made after', options=options, index=None, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ is None or input_ == '':
            return False, 'Please select a previous state.'
        return True, ''


class CommentField(Field):
    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        return st.text_area('Comment', value=prefill, width=99999)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class PhaseDurationField(UnitField):
    type = Ft.MANDATORY
    ui_unit = ur.seconds

    def _streamlit_input(self, prefill, key: str):
        return st.number_input(f'Phase duration ({self.ui_unit:P})',
                               min_value=0., value=prefill, key=key, width=150)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == 0:
            return False, 'Duration must be strictly positive.'
        return True, ''


class PumpingDurationField(UnitField):
    type = Ft.MANDATORY
    ui_unit = ur.minutes

    def _streamlit_input(self, prefill, key: str):
        return st.number_input(f'Pumping duration ({self.ui_unit:P})',
                               min_value=0., value=prefill, width=200)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == 0:
            return False, 'Duration must be strictly positive.'
        return True, ''


class PressureField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.millibar

    def _streamlit_input(self, prefill, key: str):
        return st.number_input(f'Pressure ({self.ui_unit:P})',
                               min_value=0., width=150)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == 0:
            return False, 'Pressure must be strictly positive.'
        return True, ''


class AnnealingAtmosphereField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        return st.text_input(
            'Atmosphere stoichiometry:', value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return Patch.is_valid_formula(self._input)


class FlowField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.cm**3 / ur.min
    ui_unit_alias = 'SCCM'

    def _streamlit_input(self, prefill, key: str):
        return st.number_input(f'Flow ({self.ui_unit_alias})', min_value=0., )

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == 0:
            return False, 'Flow must be strictly positive.'
        return True, ''


class AngleField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.degrees

    def _streamlit_input(self, prefill, key: str):
        return st.number_input(f'Angle ({self.ui_unit:P})', )

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class RotationField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.degrees

    def _streamlit_input(self, prefill, key: str):
        return st.number_input(f'Rotation ({self.ui_unit:P})', )

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class PatternField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        options = ['pattern_2025_02_19.png']
        return st.selectbox('Pattern', options=options,
                            )

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ is None or input_ == '':
            return False, 'Please select a pattern.'
        return True, ''


class FurnaceField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        options = [f.value for f in Furnace]
        return st.selectbox('Furnace', options, index=None,
                            )

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ is None or input_ == '':
            return False, 'Please select a furnace.'
        return True, ''


class PowerField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.watt

    def _streamlit_input(self, prefill, key: str):
        return st.number_input(f'Power ({self.ui_unit:P})', min_value=0., )

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ is None or input_ <= 0.:
            return False, 'Power must be strictly positive.'
        return True, ''


class ReachedTempField(UnitField):
    type = Ft.MANDATORY
    ui_unit = ur.celsius

    def __init__(self, key: str|int = 'default_key', *, form_default,
                 db_default=None, disabled: bool):
        self.disabled = disabled  # Adding this parameter to the init method.
        super().__init__(
            key=key,
            form_default=form_default,
            db_default=db_default,
        )

    def _streamlit_input(self, prefill, key):
        unit_str = f'{self.ui_unit:~P}'
        # unit_str = f'{self.ui_unit:~P}'
        return st.number_input(f"Reached temperature ({unit_str}):",
                               value=prefill,
                               key=key, disabled=self.disabled, width=175)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class PhaseTypeField(Field):
    type = Ft.MANDATORY

    class Options(StrEnum):
        RAMP = 'Ramp'
        PLATEAU = 'Plateau'

    def _streamlit_input(self, prefill, key: str):
        options = list(self.Options)
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.radio(
            'Annealing phase type', options=options, index=index, key=key,
            horizontal=True
        )

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class PhaseCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        return st.number_input('Number of annealing phases', min_value=0,
                               value=prefill, step=1, width=200)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ < 2:
            return False, (
                'There must be at least 2 phases: room temperature to annealing'
                ' temperature, then back to room temperature.'
            )
        return True, ''


class IsRoomTemperatureField(Field):
    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        return st.checkbox('**Goes to room temperature**',
                           value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class PlasmaFormulaField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        return st.text_input('Formula',
                             key=key, value=ChemicalElement.ARGON)

    def _validate(self, input_) -> tuple[bool, str]:
        return Patch.is_valid_formula(input_)


class AcidFormulaField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        return st.text_input('Formula',
                             key=key, placeholder='H2O')

    def _validate(self, input_) -> tuple[bool, str]:
        return Patch.is_valid_formula(input_)


class AcidProportionField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        return st.number_input('Proportion (will be normalized)', min_value=0.,
                               key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Proportion must be strictly positive.'
        return True, ''


class PlasmaProportionField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        return st.number_input(
            'Proportion (will be normalized)', min_value=0., value=1,
            key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Proportion must be strictly positive.'
        return True, ''


class ConstituentCountField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        return st.number_input('Number of constituents', value=1,
                               step=1, min_value=1)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ < 1:
            return False, 'There must be at least 1 constituent.'
        return True, ''