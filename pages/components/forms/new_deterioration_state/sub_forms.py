"""Root form of the "new deterioration state" page
(`pages/new_deterioration_state.py`).

A deterioration state is a dated photo of a target with its patches
(see `DeteriorationState`). This form first makes sure the change is
really wear, then reuses `DeteriorationStateForm` from the "new target"
forms.
"""

import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_deterioration_state.fields import MadeByField, \
    IsItReallyDeteriorationField as Iirdf
from components.forms.new_target.sub_forms import DeteriorationStateForm
from logic.constants import CookieKeys as Ck
from logic.cookie_init import cookies
from logic.lab_modelization.db_models import Target, DeteriorationState


class RootForm(Form):
    """The whole "new deterioration state" form.

    Attributes:
        state: The unsaved `DeteriorationState`, with its patches and
            photo, ready for `save_with_dependent()`.
        target_img: The cropped target photo.
    """

    def __init__(self, target: Target, default_state: DeteriorationState|None):
        """Draw the title, the wear question, the author and the state.

        Reads the "last email used" cookie (a small value the browser
        stores for the app between visits) to prefill the author.

        Args:
            target: The target that gets a new state.
            default_state: State to prefill from, or None. The page
                always passes None.

        Raises:
            PausePageRun: While the wear question is not answered, if
                the answer is "human intervention" (the user is told to
                create a new target instead), and from
                `DeteriorationStateForm` while the state is incomplete.
        """
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
        email_fld = MadeByField(
            form_default=cookies.get(Ck.LAST_EMAIL_USED),
            db_default=default_state.made_by_email
                if default_state else None,
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
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''
