import streamlit as st

from logic.db_schema import Library, Film, Target, Patch, Substrate
from logic.db_enums import SputteringSystem, FilmLayerFunction, MagnetronSputteringGenerator
from logic.form_fields.shared import FormField
from logic.functions import is_valid_email_address


class LibNameField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_input("Library Name", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value in Library.already_taken_names():
            return False, "This name is already taken."
        if self.value == '':
            return False, "Please enter a name."
        return True, ''


class FilmPhysicalNameField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_input("Film name as written on the sample",
                             on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value in Film.already_taken_names():
            return False, ("This name is already used. A library corresponding to this sample"
                           "might have already been created.")
        if self.value == '':
            return False, "Please enter a name."
        return True, ''


class CommentField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_area("Comment (optional)", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class MadeOnField(FormField):
    default_value = None

    def _streamlit_input(self):
        return st.date_input("Made on", on_change=self.on_change, max_value='today')

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class MadeByField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_input("Made by (email address)", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if not is_valid_email_address(self.value):
            return False, 'Please enter a valid email address.'
        return True, ''


class ZipUploadField(FormField):
    default_value = None

    def _streamlit_input(self):
        return st.file_uploader("Upload data as a zip file.", on_change=self.on_change,
                                type=["zip"])

    def _is_valid(self) -> tuple[bool, str]:
        if self.value is None:
            return False, 'Please upload a zip file.'
        else:
            return True, ''


class SputteringSystemField(FormField):
    default_value = ''

    def _streamlit_input(self):
        options = [s.value for s in SputteringSystem]
        return st.selectbox("Sputtering system", options=options, on_change=self.on_change,
                     index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please enter select an option.'
        return True, ''


class SubstrateField(FormField):
    default_value = ''

    def _streamlit_input(self):
        options = Substrate.already_taken_names()
        return st.selectbox("Substrate", options=options, on_change=self.on_change,
                            index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please select a substrate.'
        return True, ''


class TargetField(FormField):
    default_value = ''

    def _streamlit_input(self):
        options = Target.already_taken_names()
        return st.selectbox("Target", options=options, on_change=self.on_change, index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please enter select a target.'
        return True, ''


class StoichiometryField(FormField):
    default_value = ''
    def _streamlit_input(self):
        return st.text_input("Stoichiometry", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return Patch.is_valid_stoichio(self.value)


class FilmLayerFunctionField(FormField):
    default_value = ''

    def _streamlit_input(self):
        function_options = [f.value for f in FilmLayerFunction]
        return st.selectbox("Layer function", options=function_options,
                            on_change=self.on_change, index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please select an option.'
        return True, ''


class DepositDistanceField(FormField):
    default_value = 100.

    def _streamlit_input(self):
        return st.number_input("Deposit distance", min_value=0, on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == 0:
            return False, 'Deposit distance must be strictly positive.'
        return True, ''


class DepositAngleField(FormField):
    default_value = 0.

    def _streamlit_input(self):
        return st.number_input("Deposit angle", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class SputteringGeneratorField(FormField):
    default_value = ''

    def _streamlit_input(self):
        options = [gen.value for gen in MagnetronSputteringGenerator]
        return st.selectbox("Sputtering generator", options=options,
                            on_change=self.on_change, index=None)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please select an option.'
        return True, ''


class HasActiveCoolingField(FormField):
    default_value = True

    def _streamlit_input(self):
        return st.radio("Has active cooling", on_change=self.on_change, index=None,
                        options=[True, False], horizontal=True)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '' or self.value is None:
            return False, 'Please select an option.'
        return True, ''


# has_active_cooling_F: bool = True
# rotation_F: num = 0
# filament_tension_F: num = 170

class RotationField(FormField):
    default_value = 0

    def _streamlit_input(self):
        return st.number_input("Rotation", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class FilamentTensionField(FormField):
    default_value = 0.

    def _streamlit_input(self):
        return st.number_input("Filament tension", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''