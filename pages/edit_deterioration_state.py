import streamlit as st

from components.forms.edit_deterioration_state.sub_forms import RootForm
from components.forms.base_classes import PausePageRun
from components.streamlit_tools import sess, init_page, \
    switch_to_submit_successful, current_params
from logic.constants import CookieKeys as Ck, FILE_STORAGE_PATH, \
    IdType
from logic.functions import save_cookies
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
        sess[Ck.LAST_EMAIL_USED] = new_state.made_by_email

        with db.atomic():
            old_state.delete_instance(recursive=True)
            new_state.save_with_dependent()
            photo_path = FILE_STORAGE_PATH / new_state.photo_file_name
            root_form.target_img.save(photo_path)

        save_cookies()
        switch_to_submit_successful(
            redirect_to=pages.inspect_target,
            id_type=IdType.TARGET,
            object_id=target.id,
        )

except PausePageRun:
    pass

