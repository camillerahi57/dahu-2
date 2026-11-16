"""Page for adding a new library: its film, targets and layers.

The whole form is `new_library.sub_forms.RootForm`. On submit, the
library, its film, the film's layers and their parts are saved in one
transaction (a group of DB writes that either all succeed or are all
cancelled), with an `AppLog` row for the library. The user is then
sent to the new library's page.
"""
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
    st.title('New Library')
    st.divider()
    # `RootForm` raises `PausePageRun` while the library, film or
    # layers are invalid, so the button only appears once they are
    # valid. It stays disabled until the rest is valid too, e.g. the
    # "layers are in the right order" box.
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