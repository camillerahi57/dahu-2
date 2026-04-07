from logic.db_schema import Patch, Substrate
from logic.form_fields.shared import FormField
import streamlit as st


class StoichiometryField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_input("Stoichiometry", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return Patch.is_valid_stoichio(self.value)


class CommentField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_area("Comment (optional)", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class SubstrateNameField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_input("Substrate Name", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value == '':
            return False, 'Enter a substrate name.'
        if self.value in Substrate.already_taken_names():
            return False, 'Name already taken.'
        return True, ''


class ThicknessField(FormField):
    default_value = None

    def _streamlit_input(self):
        return st.number_input("Thickness", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value <= 0:
            return False, 'Thickness must be strictly positive.'
        return True, ''

class HField(FormField):
    default_value = 0

    def _streamlit_input(self):
        return st.number_input("H", step=1, on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''

class KField(FormField):
    default_value = 0

    def _streamlit_input(self):
        return st.number_input("K", step=1, on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''

class LField(FormField):
    default_value = 0

    def _streamlit_input(self):
        return st.number_input("L", step=1, on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''
