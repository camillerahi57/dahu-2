from datetime import datetime
from enum import StrEnum
from uuid import uuid4

import streamlit as st

from components.forms.shared2 import Field, FieldType as Ft
from logic.constants import CookieKeys as Ck, NEW_TARGET
from logic.db_enums import ShapeType
from logic.functions import is_valid_email_address
from logic.lab_modelization.db_models import Target, Patch


class MadeAtField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default: datetime = None):
        default = 'today' if default is None else default
        return st.date_input("First made on", value=default)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class ExperimenterEmailField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default: str = ''):
        cookie_email = st.session_state.get(Ck.LAST_EMAIL_USED, '')
        default = cookie_email if default == '' else default
        return st.text_input(
            "First made by (email address)",
            value=default, width=500)

    def _validate(self) -> tuple[bool, str]:
        if not is_valid_email_address(self._input):
            return False, 'Please enter a valid email address.'
        st.session_state[Ck.LAST_EMAIL_USED] = self._input
        return True, ''


class TargetNameField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default: str = None):
        return st.text_input("Target name", width=600, value=default)

    def _validate(self) -> tuple[bool, str]:
        if len(self._input) == 0:
            return False, 'Please enter a target name.'
        is_already_taken = self._input in Target.already_taken_names()
        is_default = self._input == self.default
        if is_already_taken and not is_default:
            return False, "Target name already taken."
        return True, ''


class PatchCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.number_input(
            "Number of patches (including base patch)",
                  min_value=0, value=default,
                  step=1, width=300)

    def _validate(self) -> tuple[bool, str]:
        if self._input < 1:
            return False, 'Please add at least one patch.'
        return True, ''


class ShapeField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        options = [ShapeType.DISC, ShapeType.POLYGON]
        idx = options.index(default) if default is not None else None
        return st.radio(
            label='Patch shape', label_visibility='collapsed',
            options=options,
            index=idx, key=self.key, horizontal=True)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class VertexCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        default = 3 if default is None else default
        return st.number_input("Number of vertices for the polygon",
                               min_value=3, step=1, width=300, value=default,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class CommentField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.text_area("Comment about the target", width=99999,
                            value=default, label_visibility="collapsed")

    def _validate(self) -> tuple[bool, str]:
        if self._input == '':
            return False, 'Please enter a comment.'
        return True, ''


class StoichiometryField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.text_input("Stoichiometry", width=300, key=self.key,
                             label_visibility='collapsed',
                             placeholder='Stoichiometry', value=default)

    def _validate(self) -> tuple[bool, str]:
        return Patch.is_valid_formula(self._input)


class IsBasePatchField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=False):
        return st.checkbox("Is the base patch of the target.",
                           value=default, key=self.key)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


# TODO Forbid negative pixels everywhere.

class IsCorrectFigureField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=False):
        return st.checkbox("**The figure matches the picture "
                           "of the target.**",
                           value=default, key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if not self._input:
            return False, ("Please ensure the figure matches the target "
                           "picture.")
        return True, ''


class HasCorrectOrientationField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=False):
        return st.checkbox("**The picture has been taken properly "
                           "(not tilted or rotated by 90°).**",
                           value=default, key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if not self._input:
            return False, ("If the picture is tilted, edit it on your "
                           "phone or computer.")
        return True, ''


class CoordinateField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default: str=None):
        return st.text_input("X, Y", width=100, key=self.key,
                             label_visibility='collapsed', placeholder='X, Y',
                             value=default)

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

    def _streamlit_input(self, default: str = None):
        names = Target.already_taken_names()
        options = [NEW_TARGET] + names
        if default is None:
            idx = None
        else:
            idx = options.index(default)

        return st.selectbox('Built from other target:', options=options,
                                index=idx, width=300)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class HasCommentField(Field):
    type = Ft.MANDATORY

    class Option(StrEnum):
        YES = 'Yes'
        NO = 'No'

    def _streamlit_input(self, default: str = None):
        options = list(self.Option)
        index = options.index(default) if default else None
        return st.radio('No label', options, horizontal=True,
                        index=index, label_visibility='collapsed', )

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class CalibrationFactorField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, default=None):
        return st.number_input("Calibration factor", width=150,
                               value=default, step=0.1)
        # TODO Any constraints on that?

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Calibration factor must be strictly positive.'
        return True, ''


class PhotoDateField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        default = 'today' if default is None else default
        return st.date_input("Picture taken on", max_value='today',
                             value=default, width=150)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class PhotoUploadField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.file_uploader("Select target photo",
                                type=["jpg", "png"])

    def _validate(self) -> tuple[bool, str]:
        if self._input is None:
            return False, 'Please upload an image file.'
        else:
            return True, ''

    def new_file_name(self):
        extension = self._input.name.split('.')[-1]
        return f'{uuid4()}.{extension}'


class PixelEquivalenceField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.number_input("Is equivalent to (pixels):",
                               min_value=0, step=1, value=default)

    def _validate(self) -> tuple[bool, str]:
        if self._input == 0:
            return False, ('[Mandatory] Please enter the equivalent distance'
                           ' in pixels.')
        return True, ''


class MillimeterEquivalenceField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, default=None):
        return st.number_input("Distance in millimeters:",
                               min_value=0, step=1, value=default)

    def _validate(self) -> tuple[bool, str]:
        if self._input == 0:
            return False, ('[Mandatory] Please enter a distance in millimeters'
                           ' for which '
                           'you know the equivalent in pixels.')
        return True, ''
