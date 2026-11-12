"""Page for editing a target's deterioration state (photo and patches).

The state is chosen by the `state_id` query parameter (a `name=value`
pair after the `?` of the URL, see `IdType.STATE`). The form is
`edit_deterioration_state.sub_forms.RootForm`, prefilled from the
state. On submit, the state is replaced as a whole in one transaction
(a group of DB writes that either all succeed or are all cancelled):
the old state, its patches and its photo are deleted, then the new
ones are saved. The new state gets a new id, and its photo a new file
in `user_data/`. Both steps write `AppLog` rows.
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.edit_deterioration_state.sub_forms import RootForm
from components.general import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Target, DeteriorationState
from logic.page_list import pages

init_page(pages.edit_state)

state_id = current_params()[IdType.STATE]
old_state: DeteriorationState = DeteriorationState.get_by_id(state_id)
target: Target = old_state.target

st.set_page_config(layout='centered')

try:
    root_form = RootForm(target, default_state=old_state)
    new_state = root_form.state

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        with db.atomic():
            # TODO: Fix this:
            # Also deletes the old photo file at once; a later failure
            # cancels the DB writes but cannot bring the file back.
            # The new photo keeps its bytes in memory.
            old_state.delete_with_parts()
            new_state.save_with_dependent()
            # `save_with_dependent` only writes DB rows; the photo's
            # bytes are written to `user_data/` here.
            new_state.photos[0].save_bytes()

        switch_to_submit_successful(
            redirect_to=pages.inspect_target,
            id_type=IdType.TARGET,
            object_id=target.id,
        )

except PausePageRun:
    pass

