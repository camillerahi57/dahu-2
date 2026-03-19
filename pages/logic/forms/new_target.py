import re

from logic.constants import StorageKeys as Sk
from logic.db_schema import Target, Patch
from logic.forms.shared import FormField
import streamlit as st


class MadeAtField(FormField):
    default_value = None

    def _streamlit_input(self):
        return st.date_input("Target made on", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class ExperimenterEmailField(FormField):
    def default_value(self):
        if Sk.LAST_EMAIL_USED in st.session_state:
            return st.session_state[Sk.LAST_EMAIL_USED]
        else:
            return ''

    def _streamlit_input(self):
        return st.text_input(
            "Made by (email address)",
            on_change=self.on_change,
            value=self.default_value()
        )

    def _is_valid(self) -> tuple[bool, str]:
        # From https://stackoverflow.com/a/201378:
        email_regex = r"(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
        if re.fullmatch(email_regex, self.value) is None:
            return False, "Please enter a valid email address."
        else:
            return True, ''


class TargetNameField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_input("Target name", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        if len(self.value) == 0:
            return False, 'Please enter a target name.'
        if self.value in Target.already_taken_names():
            return False, "Target name already taken."
        return True, ''


class CommentField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_input("Comment (optional)", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class StoichiometryField(FormField):
    default_value = ''

    def _streamlit_input(self):
        return st.text_input("Stoichiometry", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return Patch.is_valid_stoichio(self.value)


class DiscCenterX(FormField):
    default_value = None

    def _streamlit_input(self):
        return st.number_input("Center X coordinate", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class DiscCenterY(FormField):
    default_value = None

    def _streamlit_input(self):
        return st.number_input("Center Y coordinate", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RadiusField(FormField[float]):
    default_value = 0.

    def _streamlit_input(self):
        return st.number_input(
            "Disc radius", on_change=self.on_change, value=self.default_value
        )

    def _is_valid(self):
        if self.value > 0:
            return True, ''
        else:
            return False, f'Radius must be strictly positive.'


class RectangleFirstVertexX(FormField[float]):
    default_value = 0.

    def _streamlit_input(self):
        return st.number_input("First vertex X position", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RectangleFirstVertexY(FormField[float]):
    default_value = 0.

    def _streamlit_input(self):
        return st.number_input("First vertex Y position", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RectangleOppositeVertexX(FormField[float]):
    default_value = 0.

    def _streamlit_input(self):
        return st.number_input("Opposite vertex X position", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''


class RectangleOppositeVertexY(FormField[float]):
    default_value = 0.

    def _streamlit_input(self):
        return st.number_input("Opposite vertex Y position", on_change=self.on_change)

    def _is_valid(self) -> tuple[bool, str]:
        return True, ''