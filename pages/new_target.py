"""Page for adding a new sputtering target with its first
deterioration state (photo and patches).

The whole form is `new_target.sub_forms.RootForm`. On submit, the
target, its state, the state's photo row and its patches are saved in
one transaction (a group of DB writes that either all succeed or are
all cancelled), with `AppLog` rows. The photo itself is written to
`user_data/`. The user is then sent to the new target's page.
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_target.sub_forms import RootForm
from components.general import init_page, \
    switch_to_submit_successful
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.page_list import pages

init_page(pages.new_target)

st.set_page_config(layout='centered')

try:
    root_form = RootForm()
    target = root_form.target

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        with db.atomic():

            target.save_with_dependent()
            # `save_with_dependent` only writes DB rows; the photo's
            # bytes must be written to `user_data/` separately. Done
            # inside the transaction so that a failure here cancels the
            # rows too.
            target.states[0].photos[0].save_bytes()
        switch_to_submit_successful(
            redirect_to=pages.inspect_target,
            id_type=IdType.TARGET,
            object_id=target.id,
        )

except PausePageRun:
    pass

