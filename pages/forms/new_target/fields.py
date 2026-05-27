from uuid import uuid4

import streamlit as st

from logic.constants import CookieKeys as Ck, NEW_TARGET
from logic.db_enums import ShapeType
from logic.lab_modelization.db_models import Target, Patch
from forms.shared2 import Field, FieldType as Ft
from logic.functions import is_valid_email_address


class MadeAtField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.date_input("Target made on")

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class ExperimenterEmailField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        default_email = st.session_state.get(Ck.LAST_EMAIL_USED, '')
        return st.text_input(
            "Made by (email address)",
            value=default_email, width=500)

    def _validate(self) -> tuple[bool, str]:
        if not is_valid_email_address(self._input):
            return False, 'Please enter a valid email address.'
        st.session_state[Ck.LAST_EMAIL_USED] = self._input
        return True, ''


class TargetNameField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.text_input("Target name", width=600)

    def _validate(self) -> tuple[bool, str]:
        if len(self._input) == 0:
            return False, 'Please enter a target name.'
        if self._input in Target.already_taken_names():
            return False, "Target name already taken."
        return True, ''


class NbOfDiscField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.number_input("Number of disc patches", min_value=0,
                               step=1, width=125)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class NbOfPatchField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
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

    def _streamlit_input(self):
        return st.radio(
            label='Patch shape', label_visibility='collapsed',
            options=[ShapeType.DISC, ShapeType.POLYGON],
            index=None, key=self.key, horizontal=True)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class NbOfPolygonField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.number_input("Number of polygon patches", min_value=0,
                               step=1, width=125)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class NbOfVertexField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.number_input("Number of vertices for the polygon",
                               min_value=3, step=1, width=300, value=3)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class CommentField(Field):
    type = Ft.OPTIONAL

    def _streamlit_input(self):
        return st.text_area("Comment about the target", width=99999)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class StoichiometryField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.text_input("Stoichiometry", width=300, key=self.key,
                             label_visibility='collapsed',
                             placeholder='Stoichiometry')

    def _validate(self) -> tuple[bool, str]:
        return Patch.is_valid_formula(self._input)


# TODO Forbid negative pixels everywhere.


class CoordinateField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
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


class PreviousVersionField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        names = Target.already_taken_names()
        options = [NEW_TARGET] + names
        return st.selectbox('Built form old target:', options=options,
                            index=None)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class TargetDiameterInPixels(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.number_input("Target diameter in pixels", width=300,
                               min_value=0)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Target diameter must be strictly positive.'
        return True, ''


class CalibrationFactorField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self):
        return st.number_input("Calibration factor", width=150)
        # TODO Any constraints on that?

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Calibration factor must be strictly positive.'
        return True, ''


class TargetDiameterMillimeters(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.number_input("Real target diameter in millimeters:",
                               width=300, step=1)

    def _validate(self) -> tuple[bool, str]:
        if self._input < 0:
            return False, 'Target diameter must be strictly positive.'
        if self._input < 20:  # Too small, suspicious.
            return False, 'The diameter must be in millimeters.'
        if not self._input > 0:
            return False, 'Please enter the target diameter.'
        return True, ''


class PatchText(Field):
    type = Ft.MANDATORY

    EXAMPLE = ("disc / [target_stoichio] / 310,445 / 1134,454 / 708,1206\n"
               "disc / Nd / 438,383 / 505,394 / 467,454\n"
               "polygon / Fe / 925,438 / 1001,388 / 1069,471 / 1000,528\n")

    def _streamlit_input(self):
        label = "Start with a disc for the target it-self."
        return st.text_area(label,
                            placeholder=self.EXAMPLE, height=200)

    def _validate(self) -> tuple[bool, str]:
        if not self._input.strip().startswith('disc'):
            return False, 'Please start with the target disc.'
        return True, ''


class VertexXCoordinateField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.number_input(" ", min_value=0, step=1, key=self.key,
                               placeholder='X')

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class VertexYCoordinateField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.number_input(" ", min_value=0, step=1, key=self.key,
                               placeholder='Y')

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class PolygonDataText(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        instructions = """The input must be a list of vertices, 
        one on each line. Each vertex is an X,Y couple, X and Y being pixel 
        coordinates on the target photo.
    \nTriangle example:
    \n12, 48
    \n78, 15
    \n6, 5"""
        return st.text_area(instructions)

    def _validate(self) -> tuple[bool, str]:
        text = self._input
        allowed_non_blank_symbols = '.,-'
        digits = '0123456789'
        allowed_blanks = ' \n'

        allowed_non_blank = digits + allowed_non_blank_symbols
        allowed_chars = allowed_non_blank_symbols + digits + allowed_blanks

        for char in text:
            if char not in allowed_chars:
                msg = (f'Invalid character in polygons input. '
                       f'Allowed characters are: {allowed_non_blank}')
                return False, msg
        text = (text
                .replace(' ', '')  # Removes all white spaces.
                .strip(',\n')  # Allow dots at the start or end.
                )
        vertex_lines = filter(None, text.split('\n'))  # Removes empty as well.
        for vertex_line in vertex_lines:
            try:
                assert len(vertex_line.removesuffix(',').split(',')) == 2
            except AssertionError:
                return False, "All vertices must have 2 elements."
        return True, ''


class PhotoDateField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.date_input("Picture taken on", max_value='today',
                             value=None, width=150)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class PhotoUploadField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
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

    def _streamlit_input(self):
        return st.number_input("Is equivalent to (pixels):",
                               min_value=0, step=1)

    def _validate(self) -> tuple[bool, str]:
        if self._input == 0:
            return False, ('[Mandatory] Please enter the equivalent distance'
                           ' in pixels.')
        return True, ''


class MillimeterEquivalenceField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self):
        return st.number_input("Distance in millimeters:",
                               min_value=0, step=1)

    def _validate(self) -> tuple[bool, str]:
        if self._input == 0:
            return False, ('[Mandatory] Please enter a distance in millimeters'
                           ' for which '
                           'you know the equivalent in pixels.')
        return True, ''
