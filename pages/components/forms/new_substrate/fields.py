"""Input fields of the substrate form (new and edit substrate pages).

Each class is one widget; see `Field` in
`components/forms/base_classes.py` for how fields draw and validate
themselves. They are assembled in `sub_forms.py`.
"""

from typing import Literal

import streamlit as st

from components.forms.base_classes import Field, FieldType as Ft, UnitField
from logic.lab_modelization.db_models import Patch, Substrate
from logic.units import ur


class StoichiometryField(Field):
    """Mandatory text input for the chemical formula of a layer.

    Validated by `Patch.is_valid_formula`. See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw a text input. See `Field._streamlit_input`."""
        return st.text_input("Stoichiometry", key=key,
                             width=400, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Check the formula syntax. See `Field._validate`."""
        return Patch.is_valid_formula(input_)


class CommentField(Field):
    """Optional free-text comment on the substrate.

    Any text is accepted. See `Field._validate`.
    """

    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key):
        """Draw a text area; `key` is not used.

        See `Field._streamlit_input`.
        """
        return st.text_area("Comment (optional)", width=600, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any text. See `Field._validate`."""
        return True, ''


class SubstrateLabelField(Field):
    """Mandatory, unique name of the substrate.

    Refuses a name already used by another substrate. On the edit page
    the substrate's own current name (the prefill) is allowed. See
    `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw a text input; `key` is not used.

        See `Field._streamlit_input`.
        """
        return st.text_input("Substrate Name", width=400, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse empty or already taken names. See `Field._validate`.

        Side effect: queries the DB for all substrate labels.
        """
        if input_ == '':
            return False, 'Enter a substrate name.'
        is_default = input_ == self.prefill
        if input_ in Substrate.already_taken_names() and not is_default:
            return False, 'Name already taken.'
        return True, ''


class ThicknessField(UnitField):
    """Mandatory thickness of a substrate layer, typed in µm.

    Stored in the DB in m. Must be strictly positive. See
    `Field._validate`.
    """

    type = Ft.MANDATORY
    ui_unit = ur.um

    def _streamlit_input(self, prefill, key):
        """Draw a number input in µm. See `Field._streamlit_input`."""
        return st.number_input(
            f"Thickness (**{self.ui_unit}**)",
            step=1., format="%.5f", key=key, width=200, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse zero or negative values. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Thickness must be strictly positive.'
        return True, ''

class HField(Field):
    """Integer h Miller index of a layer's crystal orientation.

    Any integer is accepted here; `CrystalOrientationForm` refuses
    (0, 0, 0). See `Field._validate`.

    Attributes:
        HKL_WIDTH: Widget width shared by `HField`, `KField` and
            `LField`; `'stretch'` fills the column they are put in.
    """

    type = Ft.MANDATORY

    HKL_WIDTH: Literal["stretch"] = 'stretch'

    def _streamlit_input(self, prefill, key):
        """Draw an integer input. See `Field._streamlit_input`."""
        return st.number_input("H", step=1, key=key,
                               width=HField.HKL_WIDTH, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any integer. See `Field._validate`."""
        return True, ''

class KField(Field):
    """Integer k Miller index. Same rules as `HField`."""

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw an integer input. See `Field._streamlit_input`."""
        return st.number_input("K", step=1, key=key,
                               width=HField.HKL_WIDTH, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any integer. See `Field._validate`."""
        return True, ''

class LField(Field):
    """Integer l Miller index. Same rules as `HField`."""

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw an integer input. See `Field._streamlit_input`."""
        return st.number_input("L", step=1, key=key,
                               width=HField.HKL_WIDTH, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any integer. See `Field._validate`."""
        return True, ''

class HasCrystalOrientationField(Field):
    """Yes/no radio: does the layer have a crystal orientation?

    The h, k, l fields are shown only when the answer is True. See
    `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw a True/False radio, with nothing selected if `prefill`
        is None.

        See `Field._streamlit_input`.
        """
        options = [True, False]
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.radio("Has a crystal orientation", options=options,
                        key=key, index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a choice. See `Field._validate`."""
        # Never reached with None in practice: `Field.__init__` treats
        # None as "not filled" and doesn't call `_validate`.
        if input_ is None:
            return False, "Please select an option."
        return True, ''


class LayerCountField(Field):
    """Number of layers of the substrate, at least 1.

    See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw an integer input; `key` is not used.

        See `Field._streamlit_input`.
        """
        return st.number_input("Number of layers", step=1, width=150,
                               value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse zero or negative counts. See `Field._validate`."""
        if input_ <= 0:
            return False, "A substrate must have at least 1 layer."
        return True, ''
