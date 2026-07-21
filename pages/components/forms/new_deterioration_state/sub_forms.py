from components.forms.new_deterioration_state.fields import UpdaterEmailField, \
    IsItReallyDeteriorationField as Iirdf
from components.forms.new_target.sub_forms import DeteriorationStateForm
from components.forms.shared2 import Form, PausePageRun
from logic.lab_modelization.db_models import Target, DeteriorationState
import streamlit as st


class RootForm(Form):
    def __init__(self, target: Target, default_state: DeteriorationState|None):
        st.title(f'{target.label}: New Deterioration State')

        st.write("Is this new state the result of an unwanted change, like "
                 "the target"
                 " being damaged after many uses? Or is it the "
                 "result of a human intervention, like cleaning, "
                 "adding a patch, etc.?")
        really_deterioration_fld = Iirdf(
            form_default=False
        )
        if really_deterioration_fld.value is None:
            raise PausePageRun
        elif really_deterioration_fld.value is Iirdf.Option.HUMAN:
            st.warning("Please create a new target. When you create it, you can"
                     " indicate that it's based on the current one.\n\n"
                     "A new deterioration state is only for changes that are "
                     "unwanted, due to normal usage of the target.")
            raise PausePageRun
        else:
            pass
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
