"""Root form of the "edit deterioration state" page
(`pages/edit_deterioration_state.py`).

Same as the "new deterioration state" form, without the "is it really
wear?" question, and prefilled from the existing state. The page then
replaces the old state as a whole: it deletes it with its parts and
saves the new one.
"""

import streamlit as st

from components.forms.base_classes import Form
from components.forms.new_deterioration_state.fields import MadeByField
from components.forms.new_target.sub_forms import DeteriorationStateForm
from logic.constants import CookieKeys as Ck
from logic.cookie_init import cookies
from logic.lab_modelization.db_models import Target, DeteriorationState


class RootForm(Form):
    """The whole "edit deterioration state" form.

    Attributes:
        state: The new, unsaved `DeteriorationState`, with its patches
            and photo, ready for `save_with_dependent()`.
        target_img: The cropped target photo.
    """

    def __init__(self, target: Target, default_state: DeteriorationState|None):
        """Draw the title, the author and the prefilled state.

        The author is prefilled from `default_state`, or else from the
        "last email used" cookie (a small value the browser stores for
        the app between visits).

        Args:
            target: The target the state belongs to.
            default_state: The state being edited. Despite the type
                hint, it must not be None: the title reads its date.

        Raises:
            PausePageRun: From `DeteriorationStateForm`, while the state
                is incomplete.
        """
        st.title(f'Editing state {default_state.date} of '
                 f'{target.label}')

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
