from uuid import uuid4

import streamlit as st

from logic.constants import CookieKeys as Ck
from logic.db_schema import Target, Patch
from logic.form_fields.shared import FormField
from logic.functions import is_valid_email_address


class MadeAtField(FormField):
    def _streamlit_input(self):
        return st.date_input("Target made on", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class ExperimenterEmailField(FormField):
    def _streamlit_input(self):
        if Ck.LAST_EMAIL_USED in st.session_state:
            default_email = st.session_state[Ck.LAST_EMAIL_USED]
        else:
            default_email = ''
        return st.text_input(
            "Made by (email address)", on_change=self.on_change,
            value=default_email)

    def _is_valid(self) -> tuple[bool, str]:
        if not is_valid_email_address(self.value):
            return False, 'Please enter a valid email address.'
        return True, ''


class TargetNameField(FormField):
    def _streamlit_input(self):
        return st.text_input("Target name", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if len(self.value) == 0:
            return False, 'Please enter a target name.'
        if self.value in Target.already_taken_names():
            return False, "Target name already taken."
        return True, ''


class CommentField(FormField):
    def _streamlit_input(self):
        return st.text_area("Comment (optional)", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class StoichiometryField(FormField):
    def _streamlit_input(self):
        return st.text_input("Stoichiometry", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return Patch.is_valid_stoichio(self.value)


class DiscCenterX(FormField):
    def _streamlit_input(self):
        return st.number_input("Center X (in pixels)", on_change=self.on_change,
                               step=1)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class DiscCenterY(FormField):
    def _streamlit_input(self):
        return st.number_input("Center Y (in pixels)", on_change=self.on_change,
                               step=1)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RadiusField(FormField):
    def _streamlit_input(self):
        return st.number_input(
            "Radius (in pixels)", on_change=self.on_change, step=1
        )

    def _is_valid(self):
        if self.value > 0:
            return True, ''
        else:
            return False, f'Radius must be strictly positive.'


class RectangleFirstVertexX(FormField):
    def _streamlit_input(self):
        return st.number_input("X position (in pixels)",
                               on_change=self.on_change, step=1)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RectangleFirstVertexY(FormField):
    def _streamlit_input(self):
        return st.number_input("Y position (in pixels)",
                               on_change=self.on_change, step=1)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RectangleOppositeVertexX(FormField):
    def _streamlit_input(self):
        return st.number_input("X position (in pixels)",
                               on_change=self.on_change, step=1, key='xpos')

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RectangleOppositeVertexY(FormField):
    def _streamlit_input(self):
        return st.number_input("Y position (in pixels)",
                               on_change=self.on_change, step=1, key='ypos')

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class TargetDiameterMillimeters(FormField):
    def _streamlit_input(self):
        return st.number_input("Target diameter (in millimeters):",
                               on_change=self.on_change,
                               width=200)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value < 0:
            return False, 'Target diameter must be strictly positive.'
        if self.value < 20:  # Too small, suspicious.
            return False, 'The diameter must be in millimeters.'
        if not self.value > 0:
            return False, 'Please enter the target diameter.'
        return True, ''


class PolygonDataText(FormField):
    def _streamlit_input(self):
        instructions = """The input must be a list of vertices, 
        one on each line. Each vertex is an X,Y couple.
    \nTriangle example:
    \n12.3, 48.3
    \n78, 15.6
    \n6.1, 5"""
        return st.text_area(instructions, on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        text = self.value
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


class PhotoUploadField(FormField):
    def _streamlit_input(self):
        return st.file_uploader("Select target photo", on_change=self.on_change,
                                type=["jpg", "png"])

    def _is_valid(self) -> tuple[bool, str]:
        if self.value is None:
            return False, 'Please upload an image file.'
        else:
            return True, ''

    def create_file_name(self):
        extension = self.value.name.split('.')[-1]
        return f'{uuid4()}.{extension}'
