import streamlit as st

from components.forms.new_deterioration_state.sub_forms import RootForm
from components.forms.shared2 import StopPageLoad
from logic.constants import CookieKeys as Ck, FILE_STORAGE_PATH, \
    TARGET_ID_URL_KEY, REDIRECT_PATH_URL_KEY, ID_KEY_URL_KEY, ID_VALUE_URL_KEY
from logic.functions import new_session_state, save_cookies
from logic.lab_modelization.db_models import db, Target
from logic.page_list import pages

target_id = st.query_params[TARGET_ID_URL_KEY]
target: Target = Target.get_by_id(target_id)

sess = new_session_state(pages.new_state)
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

        save_cookies(sess)
        st.switch_page(
            pages.submission_successful,
            query_params={
                REDIRECT_PATH_URL_KEY: pages.inspect_target.url_path,
                ID_KEY_URL_KEY: TARGET_ID_URL_KEY,
                ID_VALUE_URL_KEY: target.id,
            }
        )

except StopPageLoad:
    pass
