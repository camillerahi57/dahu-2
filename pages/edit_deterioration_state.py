import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.edit_deterioration_state.sub_forms import RootForm
from components.general import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import IdType
from logic.lab_modelization.db_models import db, Target, DeteriorationState
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
            old_state.delete_with_parts()
            new_state.save_with_dependent()
            new_state.photos[0].save_bytes()

        switch_to_submit_successful(
            redirect_to=pages.inspect_target,
            id_type=IdType.TARGET,
            object_id=target.id,
        )

except PausePageRun:
    pass

