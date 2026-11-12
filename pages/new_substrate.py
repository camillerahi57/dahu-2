"""Page for adding a new substrate and its layers.

The form is `new_substrate.sub_forms.RootForm`, also used by the edit
page. On submit, the substrate and its layers are saved in one
transaction (a group of DB writes that either all succeed or are all
cancelled), with an `AppLog` row for the substrate. The user is then
sent to the new substrate's page.
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_substrate.sub_forms import RootForm
from components.general import init_page, switch_to_submit_successful
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.page_list import pages


def body():
    """Draw the form, the layer sketch and the Submit button.

    The substrate is only built once Submit is clicked, since
    `to_substrate` expects a valid form.
    """
    init_page(pages.new_substrate)

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



try:
    body()
except PausePageRun:
    pass
