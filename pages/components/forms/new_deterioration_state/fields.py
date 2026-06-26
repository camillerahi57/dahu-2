from enum import StrEnum

import streamlit as st

from components.forms.shared2 import Field, FieldType as Ft
from logic.constants import CookieKeys as Ck
from logic.functions import is_valid_email_address


class UpdaterEmailField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        cookie_email = st.session_state.get(Ck.LAST_EMAIL_USED, '')
        prefill = cookie_email if prefill == '' else prefill
        return st.text_input(
            "Deterioration state updated by (email address)",
            value=prefill, width=500)

    def _validate(self, input_) -> tuple[bool, str]:
        if not is_valid_email_address(input_):
            return False, 'Please enter a valid email address.'
        st.session_state[Ck.LAST_EMAIL_USED] = input_
        return True, ''


class IsItReallyDeteriorationField(Field):
    type = Ft.MANDATORY

    class Option(StrEnum):
        UNWANTED = 'Unwanted change (damage/deterioration)'
        HUMAN = 'Human intervention (cleaning, new patch...)'

    def _streamlit_input(self, prefill: Option, key):
        options = list(self.Option)
        index = options.index(prefill) if prefill else None
        return st.radio('No label', options, horizontal=True,
                        index=index, label_visibility='collapsed', )

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''