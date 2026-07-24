import streamlit as st

from components.forms.new_library.sub_forms import BaseInfoForm
from components.forms.shared2 import PausePageRun
from components.streamlit_tools import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import IdType
from logic.functions import save_cookies
from logic.lab_modelization.db_models import db, Library
from logic.page_list import pages

init_page(pages.edit_lib)

lib_id = current_params()[IdType.LIB]
old_lib: Library = Library.get_by_id(lib_id)

st.set_page_config(layout='centered')

try:
    root_form = BaseInfoForm(default_lib=old_lib)
    # Copying the ID to keep the old one and update it:
    new_lib = root_form.to_library(id_=old_lib.id)

    if st.button("Submit", disabled=not root_form.is_valid, type='primary'):
        with db.atomic():
            new_lib.save()

        save_cookies()
        switch_to_submit_successful()

except PausePageRun:
    pass