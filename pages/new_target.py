import streamlit as st

from components.forms.new_target.sub_forms import RootForm
from components.forms.shared2 import StopPageLoad
from logic.constants import CookieKeys as Ck, FILE_STORAGE_PATH
from logic.functions import new_session_state, save_cookies
from logic.lab_modelization.db_models import (
    db)
from logic.page_list import pages

sess = new_session_state(pages.new_target)
st.set_page_config(layout='centered')

try:
    root_form = RootForm()
    target = root_form.target
    state = target.states[0]

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        sess[Ck.LAST_EMAIL_USED] = target.made_by_email

        with db.atomic():
            target.save_with_dependent()
            photo_path = FILE_STORAGE_PATH / state.photo_file_name
            root_form.target_img.save(photo_path)
        save_cookies(sess)
        st.switch_page('added_target.py')

except StopPageLoad:
    pass

