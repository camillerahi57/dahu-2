import streamlit as st

from logic.constants import CookieKeys as Ck
from logic.lab_modelization.db_models import Library, Film, Target, Patch, Substrate
from logic.db_enums import SputteringSystem, FilmLayerFunction, \
    MagnetronSputteringGenerator
from forms.shared import FormField
from logic.functions import is_valid_email_address


class LibNameField(FormField):
    def _streamlit_input(self):
        return st.text_input("Library Name", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value in Library.already_taken_names():
            return False, "This name is already taken."
        if self.value == '':
            return False, "Please enter a name."
        return True, ''


class FilmPhysicalNameField(FormField):
    def _streamlit_input(self):
        return st.text_input("Film name as written on the sample",
                             on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value in Film.already_taken_names():
            return False, (
                "This name is already used. A library corresponding to this "
                "sample might have already been created.")
        if self.value == '':
            return False, "Please enter a name."
        return True, ''


class CommentField(FormField):
    def _streamlit_input(self):
        return st.text_area("Comment (optional)", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class MadeOnField(FormField):
    def _streamlit_input(self):
        return st.date_input("Made on", on_change=self.on_change,
                             max_value='today')

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class MadeByField(FormField):
    def _streamlit_input(self):
        default = st.session_state.get(Ck.LAST_EMAIL_USED, '')
        return st.text_input("Made by (email address)",
                             on_change=self.on_change, value=default)

    def _is_valid(self) -> tuple[bool, str]:
        if not is_valid_email_address(self.value):
            return False, 'Please enter a valid email address.'
        return True, ''


class ZipUploadField(FormField):
    def _streamlit_input(self):
        return st.file_uploader("Upload data as a zip file.",
                                on_change=self.on_change,
                                type=["zip"])

    def _is_valid(self) -> tuple[bool, str]:
        if self.value is None:
            return False, 'Please upload a zip file.'
        else:
            return True, ''


class SputteringSystemField(FormField):
    def _streamlit_input(self):
        options = [s.value for s in SputteringSystem]
        return st.selectbox("Sputtering system", options=options,
                            on_change=self.on_change,
                            index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please enter select an option.'
        return True, ''


class SubstrateField(FormField):
    def _streamlit_input(self):
        options = Substrate.already_taken_names()
        return st.selectbox("Substrate", options=options,
                            on_change=self.on_change,
                            index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please select a substrate.'
        return True, ''


class TargetField(FormField):
    def _streamlit_input(self):
        options = Target.already_taken_names()
        return st.selectbox("Target", options=options, on_change=self.on_change,
                            index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please enter select a target.'
        return True, ''


class StoichiometryField(FormField):
    def _streamlit_input(self):
        return st.text_input("Stoichiometry", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return Patch.is_valid_formula(self.value)


class FilmLayerFunctionField(FormField):
    def _streamlit_input(self):
        function_options = [f.value for f in FilmLayerFunction]
        return st.selectbox("Layer function", options=function_options,
                            on_change=self.on_change, index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please select an option.'
        return True, ''


class DepositTempField(FormField):
    def _streamlit_input(self):
        return st.number_input("Deposit temperature (Kelvin)", min_value=0.,
                               on_change=self.on_change, value=300)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value <= 0:
            return False, 'Deposit temperature must be strictly positive.'
        return True, ''


class DepositDurationField(FormField):
    def _streamlit_input(self):
        return st.number_input("Deposit duration", min_value=0.,
                               on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value <= 0:
            return False, 'Deposit duration must be strictly positive.'
        return True, ''


class DepositPowerField(FormField):
    def _streamlit_input(self):
        return st.number_input("Deposit power", min_value=0.,
                               on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value <= 0:
            return False, 'Deposit power must be strictly positive.'
        return True, ''


class DepositDistanceField(FormField):
    def _streamlit_input(self):
        return st.number_input("Deposit distance", min_value=0.,
                               on_change=self.on_change,
                               value=100.)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == 0:
            return False, 'Deposit distance must be strictly positive.'
        return True, ''


class DepositAngleField(FormField):
    def _streamlit_input(self):
        return st.number_input("Deposit angle", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class SputteringGeneratorField(FormField):
    def _streamlit_input(self):
        options = [gen.value for gen in MagnetronSputteringGenerator]
        return st.selectbox("Sputtering generator", options=options,
                            on_change=self.on_change, index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please select an option.'
        return True, ''


class HasActiveCoolingField(FormField):
    def _streamlit_input(self):
        return st.radio("Has active cooling", on_change=self.on_change,
                        index=None,
                        options=[True, False], horizontal=True, )

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please select an option.'
        return True, ''


class RotationField(FormField):
    def _streamlit_input(self):
        return st.number_input("Rotation", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class FilamentCurrentField(FormField):
    def _streamlit_input(self):
        return st.number_input("Filament current", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value <= 0:
            return False, 'Filament current must be strictly positive.'
        return True, ''
