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
        default_email = st.session_state.get(Ck.LAST_EMAIL_USED, '')
        return st.text_input(
            "Made by (email address)", on_change=self.on_change,
            value=default_email)

    def _is_valid(self) -> tuple[bool, str]:
        if not is_valid_email_address(self.value):
            return False, 'Please enter a valid email address.'
        st.session_state[Ck.LAST_EMAIL_USED] = self.value
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
        return Patch.is_valid_formula(self.value)


class DiscCenterX(FormField):
    def _streamlit_input(self):
        return st.number_input("Center X (in pixels)", on_change=self.on_change,
                               step=1, min_value=0)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class DiscCenterY(FormField):
    def _streamlit_input(self):
        return st.number_input("Center Y (in pixels)", on_change=self.on_change,
                               step=1, min_value=0)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RadiusField(FormField):
    def _streamlit_input(self):
        return st.number_input(
            "Radius (in pixels)", on_change=self.on_change, step=1,
            min_value=0,
        )

    def _is_valid(self):
        if self.value <= 0:
            return False, f'Radius must be strictly positive.'
        return True, ''

# TODO Forbid negative pixels everywhere.

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


class TargetDiameterInPixels(FormField):
    def _streamlit_input(self):
        return st.number_input("Target diameter in pixels", width=300
                               , on_change=self.on_change, min_value=0)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value <= 0:
            return False, 'Target diameter must be strictly positive.'
        return True, ''

    def is_coherent_with_1st_patch(self, patch: Patch):
        if patch.disc is not None and self.is_valid:
            first_patch_diameter = patch.disc.radius_in_px * 2
            entered_px_diameter = self.value
            difference = abs(first_patch_diameter - entered_px_diameter)
            diff_ratio = difference / entered_px_diameter
            if diff_ratio < 0.1:
                return True
        return False

    def show_coherence_warning(self, target_patch: Patch):
        if (self.has_changed
                and self.is_valid
                and not self.is_coherent_with_1st_patch(target_patch)):
            st.warning(
                "The first patch you entered is supposed to be the target, "
                f"but it's radius is {int(target_patch.disc.radius_in_px)}, "
                f"which doesn't correspond to the diameter of {self.value} "
                f"pixels you just entered.")


class TargetDiameterMillimeters(FormField):
    def _streamlit_input(self):
        return st.number_input("Real target diameter in millimeters:",
                               on_change=self.on_change, width=300, step=1)

    def _is_valid(self) -> tuple[bool, str]:
        if self.value < 0:
            return False, 'Target diameter must be strictly positive.'
        if self.value < 20:  # Too small, suspicious.
            return False, 'The diameter must be in millimeters.'
        if not self.value > 0:
            return False, 'Please enter the target diameter.'
        return True, ''


class PatchText(FormField):
    EXAMPLE = ("disc / [target_stoichio] / 310,445 / 1134,454 / 708,1206\n"
               "disc / Nd / 438,383 / 505,394 / 467,454\n"
               "polygon / Fe / 925,438 / 1001,388 / 1069,471 / 1000,528\n")

    def _streamlit_input(self):
        label = "Start with a disc for the target it-self."
        return st.text_area(label, on_change=self.on_change,
                            placeholder=self.EXAMPLE, height=200)

    def _is_valid(self) -> tuple[bool, str]:
        if not self.value.strip().startswith('disc'):
            return False, 'Please start with the target disc.'
        return True, ''


class PolygonDataText(FormField):
    def _streamlit_input(self):
        instructions = """The input must be a list of vertices, 
        one on each line. Each vertex is an X,Y couple, X and Y being pixel 
        coordinates on the target photo.
    \nTriangle example:
    \n12, 48
    \n78, 15
    \n6, 5"""
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
