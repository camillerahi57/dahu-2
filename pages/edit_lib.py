"""Page for editing a library's label and comment.

The library is chosen by the `lib_id` query parameter (a `name=value`
pair after the `?` of the URL, see `IdType.LIB`). Its film is edited on
the "edit film" and "edit film layers" pages. On submit, the library
row is updated in place, keeping its id and archive status, with
`last_inspected_at` set to now (writes an `AppLog` row).
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_library.sub_forms import BaseInfoForm
from components.general import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Library
from logic.page_list import pages

init_page(pages.edit_lib)

lib_id = current_params()[IdType.LIB]
old_lib: Library = Library.get_by_id(lib_id)

st.set_page_config(layout='centered')

try:
    root_form = BaseInfoForm(default_lib=old_lib)
    # Copying the ID to keep the old one and update it:
    # (`save()` on an object that has an id updates that row.)
    # `to_library` raises `PausePageRun` while the form is invalid, so
    # the button below only appears once it is valid.
    new_lib = root_form.to_library(id_=old_lib.id,
                                   is_archived=old_lib.is_archived)

    if st.button("Submit", disabled=not root_form.is_valid, type='primary'):
        with db.atomic():
            new_lib.save()

        # No page to go back to: the next page only offers Home (see
        # DOC_NOTES.md).
        switch_to_submit_successful()

except PausePageRun:
    pass