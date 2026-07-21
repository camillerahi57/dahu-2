import streamlit as st

from components.forms.new_deterioration_state.fields import UpdaterEmailField
from components.forms.new_target.sub_forms import DeteriorationStateForm
from components.forms.shared2 import Form
from logic.lab_modelization.db_models import Target, DeteriorationState


class RootForm(Form):
    def __init__(self, target: Target, default_state: DeteriorationState|None):
        st.title(f'Editing state {default_state.date} of '
                 f'{target.label}')

        email_fld = UpdaterEmailField(
            form_default='',
            db_default=None
                if default_state is None
                else default_state.made_by_email,
        )
        state_form = DeteriorationStateForm(target, email_fld.value,
                                            default_state=default_state)

        self.state = state_form.state
        self.target_img = state_form.target_img

        super().__init__(
            fields=[email_fld],
            sub_forms=[state_form]
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''
