import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_library.sub_forms import RootForm
from components.general import init_page, switch_to_submit_successful
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.page_list import pages

init_page(pages.new_lib)


st.set_page_config(layout="wide")


try:
    root_form = RootForm()
    library = root_form.library

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        with db.atomic():
            library.save_with_dependent()

        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=library.id,
        )

except PausePageRun:
    pass