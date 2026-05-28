from uuid import uuid4

import streamlit as st

from components.forms.shared2 import Field, FieldType as Ft
from logic.constants import CookieKeys as Ck
from logic.db_enums import ShapeType
from logic.functions import is_valid_email_address
from logic.lab_modelization.db_models import Patch


class MadeAtField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        return st.date_input("Update day")

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class ExperimenterEmailField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        default_email = st.session_state.get(Ck.LAST_EMAIL_USED, '')
        return st.text_input(
            "Updated by (email address)",
            value=default_email, width=500)

    def _validate(self) -> tuple[bool, str]:
        if not is_valid_email_address(self._input):
            return False, 'Please enter a valid email address.'
        st.session_state[Ck.LAST_EMAIL_USED] = self._input
        return True, ''


class NbOfPatchField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        return st.number_input(
            "Number of patches (including base patch)",
                  min_value=0,
                  step=1, width=300)

    def _validate(self) -> tuple[bool, str]:
        if self._input < 1:
            return False, 'Please add at least one patch.'
        return True, ''


class ShapeField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        return st.radio(
            label='Patch shape', label_visibility='collapsed',
            options=[ShapeType.DISC, ShapeType.POLYGON],
            index=None, key=self.key, horizontal=True)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class NbOfVertexField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        return st.number_input("Number of vertices for the polygon",
                               min_value=3, step=1, width=300, value=3)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class CommentField(Field):
    type = Ft.OPTIONAL

    def _streamlit_input(self, updated=None):
        return st.text_area("Comment about this new deterioration state",
                            width=99999)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class StoichiometryField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        return st.text_input("Stoichiometry", width=300, key=self.key,
                             label_visibility='collapsed',
                             placeholder='Stoichiometry')

    def _validate(self) -> tuple[bool, str]:
        return Patch.is_valid_formula(self._input)


# TODO Forbid negative pixels everywhere.


class CoordinateField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        return st.text_input("X, Y", width=100, key=self.key,
                             label_visibility='collapsed', placeholder='X, Y')

    def _validate(self) -> tuple[bool, str]:
        try:
            x, y = eval(self._input)
            if not isinstance(x, int) or not isinstance(y, int):
                return False, 'Coordinates must be integers.'
            if x < 0 or y < 0:
                return False, 'Coordinates must be strictly positive.'
            return True, ''
        except:  # noqa
            return False, 'Invalid format.'


class CalibrationFactorField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, updated=None):
        return st.number_input("Calibration factor", width=150)
        # TODO Any constraints on that?

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Calibration factor must be strictly positive.'
        return True, ''


class PhotoUploadField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        return st.file_uploader("Select target photo",
                                type=["jpg", "png"])

    def _validate(self) -> tuple[bool, str]:
        if self._input is None:
            return False, 'Please upload an image file.'
        else:
            return True, ''

    def create_file_name(self):
        extension = self._input.name.split('.')[-1]
        return f'{uuid4()}.{extension}'


class PixelEquivalenceField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        return st.number_input("Is equivalent to (pixels):",
                               min_value=0, step=1)

    def _validate(self) -> tuple[bool, str]:
        if self._input == 0:
            return False, ('[Mandatory] Please enter the equivalent distance'
                           ' in pixels.')
        return True, ''


class MillimeterEquivalenceField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, updated=None):
        return st.number_input("Distance in millimeters:",
                               min_value=0, step=1)

    def _validate(self) -> tuple[bool, str]:
        if self._input == 0:
            return False, ('[Mandatory] Please enter a distance in millimeters'
                           ' for which '
                           'you know the equivalent in pixels.')
        return True, ''
