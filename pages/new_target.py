import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_target.sub_forms import RootForm
from components.general import init_page, \
    switch_to_submit_successful
from logic.constants import IdType
from logic.lab_modelization.db_models import (
    db)
from logic.page_list import pages

init_page(pages.new_target)

st.set_page_config(layout='centered')

try:
    root_form = RootForm()
    target = root_form.target

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        with db.atomic():

            target.save_with_dependent()
            target.states[0].photos[0].save_bytes()
        switch_to_submit_successful(
            redirect_to=pages.inspect_target,
            id_type=IdType.TARGET,
            object_id=target.id,
        )

except PausePageRun:
    pass

