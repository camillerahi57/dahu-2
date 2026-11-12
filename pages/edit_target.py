"""Page for editing a target's basic info (date, author, label,
previous version).

The target is chosen by the `target_id` query parameter (a
`name=value` pair after the `?` of the URL, see `IdType.TARGET`). Its
deterioration states are edited on their own page. On submit, the
target row is updated in place, keeping its id and archive status
(writes an `AppLog` row), and the user is sent back to the target's
page.
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_target.sub_forms import BasicInfoForm
from components.general import init_page, switch_to_submit_successful, \
    current_params
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Target
from logic.page_list import pages

init_page(pages.edit_target)

target_id = current_params()[IdType.TARGET]
old_target: Target = Target.get_by_id(target_id)

st.set_page_config(layout='centered')

try:
    root_form = BasicInfoForm(default_target=old_target)
    # Copying the ID to keep the old one and update it:
    # (`save()` on an object that has an id updates that row.)
    # `to_target` raises `PausePageRun` while the form is invalid, so
    # the button below only appears once it is valid.
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

