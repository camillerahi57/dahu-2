import streamlit as st

from components.forms.new_library.sub_forms import RootForm
from components.forms.base_classes import PausePageRun
from components.streamlit_tools import init_page, sess, \
    switch_to_submit_successful
from logic.constants import CookieKeys as Ck, IdType
from logic.functions import save_cookies
from logic.lab_modelization.db_models import db
from logic.page_list import pages

init_page(pages.new_lib)


st.set_page_config(layout="wide")


try:
    root_form = RootForm()
    library = root_form.library

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        sess[Ck.LAST_EMAIL_USED] = library.films[0].made_by_email

        with db.atomic():
            library.save_with_dependent()

        save_cookies()
        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=library.id,
        )

except PausePageRun:
    pass