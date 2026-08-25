import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_target.sub_forms import BasicInfoForm
from components.general import init_page, switch_to_submit_successful, \
    current_params
from logic.constants import IdType
from logic.lab_modelization.db_models import db, Target
from logic.page_list import pages

init_page(pages.edit_target)

target_id = current_params()[IdType.TARGET]
old_target: Target = Target.get_by_id(target_id)

st.set_page_config(layout='centered')

try:
    root_form = BasicInfoForm(default_target=old_target)
    # Copying the ID to keep the old one and update it:
    new_target = root_form.to_target(id_=old_target.id,
                                     is_archived=old_target.is_archived)

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        with db.atomic():
            new_target.save()

        switch_to_submit_successful(
            redirect_to=pages.inspect_target,
            id_type=IdType.TARGET,
            object_id=new_target.id,
        )

except PausePageRun:
    pass

