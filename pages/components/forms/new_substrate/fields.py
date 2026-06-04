from typing import Literal

from logic.lab_modelization.db_models import Patch, Substrate
from components.forms.shared2 import Field, FieldType as Ft
import streamlit as st


class StoichiometryField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, default=None):
        return st.text_input("Stoichiometry", key=self.key,
                             width=400)

    def _validate(self) -> tuple[bool, str]:
        return Patch.is_valid_formula(self._input)


class CommentField(Field):
    type = Ft.OPTIONAL

    def _streamlit_input(self, default=None):
        return st.text_area("Comment (optional)")

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class SubstrateNameField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.text_input("Substrate Name", width=400)

    def _validate(self) -> tuple[bool, str]:
        if self._input == '':
            return False, 'Enter a substrate name.'
        if self._input in Substrate.already_taken_names():
            return False, 'Name already taken.'
        return True, ''


class ThicknessField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.number_input(  # TODO more realistic example:
            "Thickness (ex: 6e-3)",
            step=1e-5, format="%.5f", key=self.key, width=200)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Thickness must be strictly positive.'
        return True, ''

class HField(Field):
    type = Ft.MANDATORY

    HKL_WIDTH: Literal["stretch"] = 'stretch'

    def _streamlit_input(self, default=None):
        return st.number_input("H", step=1, key=self.key,
                               width=HField.HKL_WIDTH)

    def _validate(self) -> tuple[bool, str]:
        return True, ''

class KField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.number_input("K", step=1, key=self.key,
                               width=HField.HKL_WIDTH)

    def _validate(self) -> tuple[bool, str]:
        return True, ''

class LField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.number_input("L", step=1, key=self.key,
                               width=HField.HKL_WIDTH)

    def _validate(self) -> tuple[bool, str]:
        return True, ''

class HasCrystalOrientationField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.radio("Has a crystal orientation", [True, False],
                        index=None, key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input is None:
            return False, "Please select an option."
        return True, ''


class LayerCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.number_input("Number of layers", step=1, width=150)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, "A substrate must have at least 1 layer."
        return True, ''