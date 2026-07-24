import streamlit as st

from components.forms.new_target.sub_forms import RootForm
from components.forms.shared2 import PausePageRun
from components.streamlit_tools import sess, init_page, \
    switch_to_submit_successful
from logic.constants import CookieKeys as Ck, FILE_STORAGE_PATH, IdType
from logic.functions import save_cookies
from logic.lab_modelization.db_models import (
    db)
from logic.page_list import pages

init_page(pages.new_target)

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
        save_cookies()
        switch_to_submit_successful(
            redirect_to=pages.inspect_target,
            id_type=IdType.TARGET,
            object_id=target.id,
        )

except PausePageRun:
    pass

