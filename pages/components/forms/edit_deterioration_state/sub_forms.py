from types import SimpleNamespace

from components.forms.new_deterioration_state.fields import UpdaterEmailField
from components.forms.new_target.sub_forms import DeteriorationStateForm
from components.forms.shared2 import Form
from logic.lab_modelization.db_models import Target, DeteriorationState
import streamlit as st


class RootForm(Form):
    def __init__(self, target: Target, default_state: DeteriorationState|None):
        class Default(SimpleNamespace):
            email = ''
            state = None

        if default_state is not None:
            Default.email = default_state.made_by_email
            Default.state = default_state

        st.title(f'Editing state {default_state.date} of '
                 f'{target.physical_name}')

        email_fld = UpdaterEmailField(default=Default.email)
        state_form = DeteriorationStateForm(target, email_fld.value,
                                            default_state=Default.state)

        self.state = state_form.state
        self.target_img = state_form.target_img

        super().__init__(
            fields=[email_fld],
            sub_forms=[state_form]
        )

    def _check_coherence(self) -> tuple[bool, str]:
        return True, ''
