import streamlit as st

from logic.constants import SessionKeys as Sk, CookieKeys as Ck
from logic.db_enums import FilmModifType, Furnace
from logic.db_schema import FilmModification, Patch
from logic.form_fields.shared import FormField
from logic.functions import is_valid_email_address


class MadeByField(FormField):
    def _streamlit_input(self):  # noqa
        if Ck.LAST_EMAIL_USED in st.session_state:
            value = st.session_state[Ck.LAST_EMAIL_USED]
        else:
            value = ''
        return st.text_input("Made by (email address)",
                             on_change=self.on_change, value=value)

    def _is_valid(self) -> tuple[bool, str]:
        if not is_valid_email_address(self.value):
            return False, 'Please enter a valid email address.'
        st.session_state[Ck.LAST_EMAIL_USED] = self.value
        return True, ''


class MadeOnField(FormField):
    def _streamlit_input(self):
        return st.date_input("Made on", on_change=self.on_change,
                             max_value='today')

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class ModifTypeField(FormField):
    def _streamlit_input(self):
        return st.selectbox('Modification type', options=FilmModifType,
                     index=None, on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value is None or self.value == '':
            return False, 'Please select a modification type.'
        return True, ''


class MadeAfterField(FormField):
    def _streamlit_input(self):
        sess = st.session_state
        film = sess[Sk.CURRENT_FILM]
        film_modifs = (FilmModification.select()
                       .where(FilmModification.film == film))
        def get_modif_nb(fm: FilmModification):
            return fm.modif_number
        film_modifs = sorted(list(film_modifs), key=get_modif_nb)
        options = [
            (modif.modif_number, modif.modif_type)
            for modif in film_modifs
        ]
        options = sorted(options, key=lambda x: x[0])
        options = [(-1, 'Film initial state')] + options
        return st.selectbox('Made after', options=options,
                                     index=None, on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value is None or self.value == '':
            return False, 'Please select a previous state.'
        return True, ''


class TemperatureField(FormField):
    def _streamlit_input(self):
        return st.number_input('Temperature', min_value=0.,
                               on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == 0:
            return False, 'Temprature must be strictly positive.'
        return True, ''


class DurationField(FormField):
    def _streamlit_input(self):
        return st.number_input('Duration', min_value=0.,
                               on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == 0:
            return False, 'Duration must be strictly positive.'
        return True, ''


class PressureField(FormField):
    def _streamlit_input(self):
        return st.number_input('Pressure', min_value=0.,
                               on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == 0:
            return False, 'Pressure must be strictly positive.'
        return True, ''


class FlowField(FormField):
    def _streamlit_input(self):
        return st.number_input('Flow', min_value=0., on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == 0:
            return False, 'Flow must be strictly positive.'
        return True, ''


class AngleField(FormField):
    def _streamlit_input(self):
        return st.number_input('Angle', on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RotationField(FormField):
    def _streamlit_input(self):
        return st.number_input('Rotation', on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class PatternField(FormField):
    def _streamlit_input(self):
        options = ['pattern_2025_02_19.png']
        return st.selectbox('Pattern', options=options,
                            on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value is None or self.value == '':
            return False, 'Please select a pattern.'
        return True, ''


class FurnaceField(FormField):
    def _streamlit_input(self):
        options = [f.value for f in Furnace]
        return st.selectbox('Furnace', options, index=None,
                            on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value is None or self.value == '':
            return False, 'Please select a furnace.'
        return True, ''


class PowerField(FormField):
    def _streamlit_input(self):
        return st.number_input('Power', min_value=0., on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value is None or self.value <= 0.:
            return False, 'Power must be strictly positive.'
        return True, ''


class PlasmaFormulaField(FormField):
    def _streamlit_input(self):
        return st.text_input('Formula', on_change=self.on_change,
                             key=self.input_key, value='Ar')

    def _is_valid(self) -> tuple[bool, str]:
        return Patch.is_valid_formula(self.value)


class AcidFormulaField(FormField):
    def _streamlit_input(self):
        return st.text_input('Formula', on_change=self.on_change,
                             key=self.input_key, placeholder='H2O')

    def _is_valid(self) -> tuple[bool, str]:
        return Patch.is_valid_formula(self.value)


class ProportionField(FormField):
    def _streamlit_input(self):
        return st.number_input('Proportion (will be normalized)', min_value=0.,
                               on_change=self.on_change, key=self.input_key)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value <= 0:
            return False, 'Proportion must be strictly positive.'
        return True, ''


class NumberOfConstituentsField(FormField):
    def _streamlit_input(self):
        return st.number_input('Number of constituents', value=1,
                               on_change=self.on_change, step=1, min_value=1)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value < 1:
            return False, 'There must be at least 1 constituent.'
        return True, ''