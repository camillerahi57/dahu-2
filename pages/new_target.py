import streamlit as st

from components.forms.new_target.sub_forms import RootForm
from components.forms.shared2 import StopPageLoad
from logic.constants import CookieKeys as Ck, FILE_STORAGE_PATH
from logic.functions import load_session_state, save_session_state
from logic.lab_modelization.db_models import (
    db)
from logic.page_list import PageEnum

sess = load_session_state(PageEnum.new_target)
st.set_page_config(layout='centered')

try:
    main_form = RootForm()
    target = main_form.target
    state = target.states[0]

    if st.button("Submit", disabled=not main_form.is_valid, type="primary"):
        sess[Ck.LAST_EMAIL_USED] = target.made_by_email

        with db.atomic():
            target.cascade_save()
            photo_path = FILE_STORAGE_PATH / state.photo_file_name
            main_form.target_img.save(photo_path)
            save_session_state(sess)
        st.switch_page('added_target.py')
except StopPageLoad:
    pass
