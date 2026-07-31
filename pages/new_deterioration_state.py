import streamlit as st

from components.forms.new_deterioration_state.sub_forms import RootForm
from components.forms.base_classes import PausePageRun
from components.streamlit_tools import init_page, sess, \
    switch_to_submit_successful, current_params
from logic.constants import CookieKeys as Ck, FILE_STORAGE_PATH, IdType
from logic.functions import save_cookies
from logic.lab_modelization.db_models import db, Target
from logic.page_list import pages

init_page(pages.new_state)

target_id = current_params()[IdType.TARGET]
target: Target = Target.get_by_id(target_id)

st.set_page_config(layout='centered')

try:
    root_form = RootForm(target, default_state=None)
    state = root_form.state

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        sess[Ck.LAST_EMAIL_USED] = state.made_by_email

        with db.atomic():
            state.save_with_dependent()
            photo_path = FILE_STORAGE_PATH / state.photo_file_name
            root_form.target_img.save(photo_path)

        save_cookies()
        switch_to_submit_successful(
            redirect_to=pages.inspect_target,
            id_type=IdType.TARGET,
            object_id=target.id,
        )

except PausePageRun:
    pass
