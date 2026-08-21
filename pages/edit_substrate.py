import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_substrate.sub_forms import RootForm
from components.general import init_page, switch_to_submit_successful, \
    current_params
from logic.constants import IdType
from logic.utils import save_cookies
from logic.lab_modelization.db_models import db, Substrate
from logic.page_list import pages

init_page(pages.new_substrate)

substrate_id = current_params()[IdType.SUB]
old_substrate: Substrate = Substrate.get_by_id(substrate_id)

try:
    root_form = RootForm(old_substrate)
    root_form.show_layers()

    st.divider()

    if st.button("Submit", disabled=not root_form.is_valid, type='primary'):
        new_substrate = root_form.to_substrate(old_substrate.id)

        with db.atomic():
            old_substrate.delete_with_parts()
            new_substrate.save_with_dependent(force_insert=True)

        save_cookies()
        switch_to_submit_successful(
            redirect_to=pages.inspect_substrate,
            id_type=IdType.SUB,
            object_id=new_substrate.id,
        )

except PausePageRun:
    pass