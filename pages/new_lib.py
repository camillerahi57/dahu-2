from components.forms.new_library.sub_forms import RootForm
from components.forms.shared2 import StopPageRun
from logic.constants import CookieKeys as Ck, REDIRECT_PATH_URL_KEY, \
    ID_KEY_URL_KEY, ID_VALUE_URL_KEY, LIB_ID_URL_KEY

import streamlit as st

from logic.functions import new_session_state, save_cookies
from logic.lab_modelization.db_models import db
from logic.page_list import pages


st.set_page_config(layout="wide")

sess = new_session_state(pages.new_lib)

try:
    root_form = RootForm()
    library = root_form.library

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        sess[Ck.LAST_EMAIL_USED] = library.films[0].made_by_email

        with db.atomic():
            library.save_with_dependent()

        save_cookies(sess)
        st.switch_page(
            pages.submission_successful,
            query_params={
                REDIRECT_PATH_URL_KEY: pages.inspect_lib.url_path,
                ID_KEY_URL_KEY: LIB_ID_URL_KEY,
                ID_VALUE_URL_KEY: library.id,
            }
        )

except StopPageRun:
    pass