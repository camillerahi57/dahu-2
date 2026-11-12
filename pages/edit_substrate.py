"""Page for editing a substrate and its layers.

The substrate is chosen by the `substrate_id` query parameter (a
`name=value` pair after the `?` of the URL, see `IdType.SUB`). The form
is the one of the "new substrate" page, prefilled. On submit, the
substrate is replaced as a whole in one transaction (a group of DB
writes that either all succeed or are all cancelled): the old row and
its layers are deleted, then the new ones are inserted with the old
substrate id. Both steps write `AppLog` rows.
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_substrate.sub_forms import RootForm
from components.general import init_page, switch_to_submit_successful, \
    current_params
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Substrate
from logic.page_list import pages

# TODO Fix: pages.edit_substrate:
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
            # The new object has the old id, so a plain `save()` would
            # try to update the row just deleted; `force_insert` makes
            # it insert instead. Deleting a substrate used by films is
            # allowed here because `Film.substrate` is declared
            # `deferrable='INITIALLY DEFERRED'`: SQLite only checks it
            # when the transaction ends, and the id exists again then.
            new_substrate.save_with_dependent(force_insert=True)

        switch_to_submit_successful(
            redirect_to=pages.inspect_substrate,
            id_type=IdType.SUB,
            object_id=new_substrate.id,
        )

except PausePageRun:
    pass