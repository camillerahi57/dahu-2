import streamlit as st

from components.forms.edit_deterioration_state.sub_forms import RootForm
from components.forms.shared2 import PausePageRun
from logic.constants import CookieKeys as Ck, FILE_STORAGE_PATH, \
    STATE_ID_URL_KEY, REDIRECT_PATH_URL_KEY, ID_KEY_URL_KEY, ID_VALUE_URL_KEY, \
    TARGET_ID_URL_KEY
from logic.functions import new_session_state, save_cookies
from logic.lab_modelization.db_models import db, Target, DeteriorationState
from logic.page_list import pages

state_id = st.query_params[STATE_ID_URL_KEY]
old_state: DeteriorationState = DeteriorationState.get_by_id(state_id)
target: Target = old_state.target

sess = new_session_state(pages.edit_state)
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
            save_cookies(sess)

        save_cookies(sess)
        st.switch_page(
            pages.submission_successful,
            query_params={
                REDIRECT_PATH_URL_KEY: pages.inspect_target.url_path,
                ID_KEY_URL_KEY: TARGET_ID_URL_KEY,
                ID_VALUE_URL_KEY: target.id,
            }
        )

except PausePageRun:
    pass

