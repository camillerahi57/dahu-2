from datetime import datetime
from enum import StrEnum

import streamlit as st

from components.forms.base_classes import Field, FieldType as Ft, UnitField
from logic.constants import NEW_TARGET
from logic.lab_modelization.db_enums import ShapeType
from logic.lab_modelization.db_models import Target, Patch
from logic.units import ur
from logic.utils import is_valid_email_address, all_email_addresses


class MadeAtField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: datetime, key):
        prefill = 'today' if prefill is None else prefill
        return st.date_input("First made on", value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class MadeByField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        options = all_email_addresses
        index = options.index(prefill) if prefill in options else None
        return st.selectbox(
            "First made by (email address)",
            options=options, index=index, accept_new_options=True, width=500)

    def _validate(self, input_) -> tuple[bool, str]:
        if not is_valid_email_address(input_):
            return False, 'Please enter a valid email address.'
        return True, ''


class TargetLabelField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        return st.text_input("Target label", width=600, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        if len(input_) == 0:
            return False, 'Please enter a target label.'
        is_already_taken = input_ in Target.already_taken_names()
        is_default = input_ == self.prefill
        if is_already_taken and not is_default:
            return False, "Target label already taken."
        return True, ''


class PatchCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        return st.number_input(
            "Number of patches (including base patch)",
                  min_value=0, value=prefill,
                  step=1, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ < 1:
            return False, 'Please add at least one patch.'
        return True, ''


class ShapeField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        options = [ShapeType.DISC, ShapeType.POLYGON]
        idx = options.index(prefill) if prefill is not None else None
        return st.radio(
            label='Patch shape', label_visibility='collapsed',
            options=options,
            index=idx, key=key, horizontal=True)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class VertexCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        prefill = 3 if prefill is None else prefill
        return st.number_input("Number of vertices for the polygon",
                               min_value=3, step=1, width=300, value=prefill,
                               key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class CommentField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        return st.text_area("Comment about the target", width=99999,
                            value=prefill, label_visibility="collapsed")

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == '':
            return False, 'Please enter a comment.'
        return True, ''


class StoichiometryField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        return st.text_input("Stoichiometry", width=300, key=key,
                             label_visibility='collapsed',
                             placeholder='Stoichiometry', value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        return Patch.is_valid_formula(input_)


class IsBasePatchField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        return st.checkbox("Is the base patch of the target.",
                           value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class IsCorrectFigureField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        return st.checkbox("**The figure matches the picture "
                           "of the target.**",
                           value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if not input_:
            return False, ("Please ensure the figure matches the target "
                           "picture.")
        return True, ''


class HasCorrectOrientationField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        return st.checkbox("**The picture has been taken properly "
                           "(not tilted or rotated by 90°).**",
                           value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if not input_:
            return False, ("If the picture is tilted, edit it on your "
                           "phone or computer.")
        return True, ''


class CoordinateField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        return st.text_input("X, Y", width=100, key=key,
                             label_visibility='collapsed', placeholder='X, Y',
                             value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        try:
            x, y = eval(input_)
            if not isinstance(x, int) or not isinstance(y, int):
                return False, 'Coordinates must be integers.'
            if x < 0 or y < 0:
                return False, 'Coordinates must be strictly positive.'
            return True, ''
        except:  # noqa
            return False, 'Invalid format.'


class PreviousVersionField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        names = Target.already_taken_names()
        options = [NEW_TARGET] + names
        if prefill is None:
            idx = None
        else:
            idx = options.index(prefill)

        return st.selectbox('Built using an existing target:',
                            options=options, index=idx, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class HasCommentField(Field):
    type = Ft.MANDATORY

    class Option(StrEnum):
        YES = 'Yes'
        NO = 'No'

    def _streamlit_input(self, prefill: str, key):
        options = list(self.Option)
        index = options.index(prefill) if prefill else None
        return st.radio('No label', options, horizontal=True,
                        index=index, label_visibility='collapsed', )

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class CalibrationFactorField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key):
        return st.text_input(
            "Calibration factor description",
            placeholder="Example: \"6 nm/C for 7.5cm and 900V\"",
            width=300,
        )

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class PhotoDateField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        return st.date_input("Picture taken on", max_value='today',
                             value=prefill, width=150)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class PhotoUploadField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        fld = st.file_uploader("Select target photo",
                                type=["jpg", "png"])
        self.file_name = fld.name if fld else None
        return fld

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ is None:
            return False, 'Please upload an image file.'
        return True, ''


class PixelEquivalenceField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        if prefill is not None:
            prefill = int(prefill)
        return st.number_input("Is equivalent to (pixels):",
                               min_value=0, step=1, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == 0:
            return False, ('[Mandatory] Please enter the equivalent distance'
                           ' in pixels.')
        return True, ''


class MillimeterEquivalenceField(UnitField):
    type = Ft.MANDATORY
    ui_unit = ur.cm

    def _streamlit_input(self, prefill, key):
        return st.number_input(f"Distance in **{self.ui_unit}**:",
                               min_value=0., step=1., value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == 0:
            return False, ('[Mandatory] Please enter a distance for which '
                           'you know the equivalent in pixels.')
        return True, ''