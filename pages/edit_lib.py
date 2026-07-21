import streamlit as st

from components.forms.new_library.sub_forms import BaseInfoForm
from components.forms.shared2 import PausePageRun
from logic.constants import REDIRECT_PATH_URL_KEY, ID_KEY_URL_KEY, \
    ID_VALUE_URL_KEY, LIB_ID_URL_KEY
from logic.functions import new_session_state, save_cookies
from logic.lab_modelization.db_models import db, Library
from logic.page_list import pages

lib_id = st.query_params[LIB_ID_URL_KEY]
old_lib: Library = Library.get_by_id(lib_id)

sess = new_session_state(pages.edit_lib)
st.set_page_config(layout='centered')

try:
    root_form = BaseInfoForm(default_lib=old_lib)
    # Copying the ID to keep the old one and update it:
    new_lib = root_form.to_library(id_=old_lib.id)

    if st.button("Submit", disabled=not root_form.is_valid, type='primary'):
        with db.atomic():
            new_lib.save()

        save_cookies(sess)
        st.switch_page(
            pages.submission_successful,
            query_params={
                REDIRECT_PATH_URL_KEY: pages.inspect_lib.url_path,
                ID_KEY_URL_KEY: LIB_ID_URL_KEY,
                ID_VALUE_URL_KEY: new_lib.id,
            }
        )

except PausePageRun:
    pass