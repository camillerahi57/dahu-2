from types import SimpleNamespace

from components.forms.new_deterioration_state.fields import UpdaterEmailField, \
    IsItReallyDeteriorationField as Iirdf
from components.forms.new_target.sub_forms import DeteriorationStateForm
from components.forms.shared2 import Form, StopPageLoad
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

        st.title(f'{target.physical_name}: New Deterioration State')

        st.write("Is this new state the result of an unwanted change, like "
                 "the target"
                 " being damaged after many uses? Or is it the "
                 "result of a human intervention, like cleaning, "
                 "adding a patch, etc.?")
        really_deterioration_fld = Iirdf()
        if really_deterioration_fld.value is None:
            raise StopPageLoad
        elif really_deterioration_fld.value is Iirdf.Option.HUMAN:
            st.warning("Please create a new target. When you create it, you can"
                     " indicate that it's based on the current one.\n\n"
                     "A new deterioration state is only for changes that are "
                     "unwanted, due to normal usage of the target.")
            raise StopPageLoad
        else:
            pass
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
