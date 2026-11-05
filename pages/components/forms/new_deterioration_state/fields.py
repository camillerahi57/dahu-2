"""Fields of the "new deterioration state" page.

`MadeByField` is also used by the "edit deterioration state" page. The
state itself (photo, scale, patches) is asked by fields from
`new_target/`.
"""

from enum import StrEnum

import streamlit as st

from components.forms.base_classes import Field, FieldType as Ft
from logic.utils import is_valid_email_address, all_email_addresses


class MadeByField(Field):
    """Mandatory email address of who records the state
    (`DeteriorationState.made_by_email`).

    The list offers every address already in the DB, but a new one can
    be typed. See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        """Draw a select box that accepts new entries; `key` is not used.

        `prefill` is selected only if it is a known address. See
        `Field._streamlit_input`.
        """
        options = all_email_addresses
        index = options.index(prefill) if prefill in options else None
        return st.selectbox(
            "Deterioration state updated by (email address)",
            options=options, index=index, accept_new_options=True, width=500)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse an invalid email address. See `Field._validate`."""
        if not is_valid_email_address(input_):
            return False, 'Please enter a valid email address.'
        return True, ''


class IsItReallyDeteriorationField(Field):
    """Mandatory question: is the new state due to wear, or to a human
    intervention?

    Not stored. It sends human interventions (cleaning, new patch...)
    to "create a new target" instead, see the page's `RootForm`. See
    `Field._validate`.
    """

    type = Ft.MANDATORY

    class Option(StrEnum):
        """The two answers shown as radio buttons."""

        UNWANTED = 'Unwanted change (damage/deterioration)'
        HUMAN = 'Human intervention (cleaning, new patch...)'

    def _streamlit_input(self, prefill: Option, key):
        """Draw horizontal radio buttons without label; `key` is not
        used.

        A falsy `prefill` (None, or the `False` the page passes) leaves
        both buttons unselected. The label is hidden because the page
        writes the question above. See `Field._streamlit_input`.
        """
        options = list(self.Option)
        index = options.index(prefill) if prefill else None
        return st.radio('No label', options, horizontal=True,
                        index=index, label_visibility='collapsed', )

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept both answers. See `Field._validate`."""
        return True, ''
