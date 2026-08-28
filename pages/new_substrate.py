import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_substrate.sub_forms import RootForm
from components.general import init_page, switch_to_submit_successful
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.page_list import pages

init_page(pages.new_substrate)

try:
    root_form = RootForm(default_sub=None)
    root_form.show_layers()

    st.divider()

    if st.button("Submit", disabled=not root_form.is_valid, type='primary'):
        substrate = root_form.to_substrate()

        with db.atomic():
            substrate.save_with_dependent()

        switch_to_submit_successful(
            redirect_to=pages.inspect_substrate,
            id_type=IdType.SUB,
            object_id=substrate.id,
        )

except PausePageRun:
    pass