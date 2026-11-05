"""Page showing one substrate: its label, its layers, and buttons to
edit or delete it.

The substrate is chosen by the `sub_id` query parameter (a
`name=value` pair after the `?` of the URL, see `IdType.SUB`). A
substrate can only be deleted when no film was deposited on it.
"""
import streamlit as st
from pandas import DataFrame

from components.forms.new_substrate.fields import ThicknessField
from components.general import init_page, switch_to_submit_successful, \
    current_params, switch_page_bttn
from components.inspection import inspect_page_header
from logic.constants import IdType
from logic.lab_modelization.db_models import Substrate, StoichioElement
from logic.page_list import pages

init_page(pages.inspect_substrate)

sub_id = current_params()[IdType.SUB]
substrate: Substrate = Substrate.get_by_id(sub_id)

st.set_page_config(layout="wide", page_title=substrate.label)


def dependent_lib_error():
    """Explain why the substrate can't be deleted, with library links.

    Shown instead of the confirmation dialog when films were deposited
    on the substrate. The message text was copied from the library
    page and talks about "characterizations" (see `DOC_NOTES.md`).
    """
    libs = substrate.libraries()
    # TODO "The substrate" instead of "The library" and "libs" instead of
    #  "characs".
    markdown = (f"The library cannot be deleted because {len(libs)} "
                f"other librarie(s) refer to some of its characterizations:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.label}]({lib_.url})"
    st.error(markdown)


@st.dialog(title="Confirm")
def confirm_deletion_dialog():
    """Ask for confirmation, then delete the substrate and its layers.

    Opens as a dialog (a pop-up window drawn over the page). On
    confirmation, deletes the substrate from the DB (writes `AppLog`
    rows) and goes to the "submission successful" page.
    """
    st.error(f"Are you sure you want to **permanently** delete the "
             f"substrate **\"{substrate.label}\"**?")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('I confirm'):
            # TODO Missing atomic. Put it inside delete_with_parts?
            substrate.delete_with_parts()
            switch_to_submit_successful(redirect_to=pages.browse_substrates)


def on_delete():
    """Handle a click on "Delete Substrate" (see `inspect_page_header`).

    Opens the confirmation dialog if no library uses the substrate,
    otherwise shows an error listing those libraries.
    """
    if substrate.can_be_deleted():
        confirm_deletion_dialog()
    else:
        dependent_lib_error()


inspect_page_header('Substrate', substrate.label, on_delete)

with st.container(horizontal_alignment='right'):
    switch_page_bttn(
        pages.edit_substrate,
        label="Edit ✏️",
        q_params={IdType.SUB: substrate.id},
        key='edit_bttn',
    )


st.divider()
st.subheader("Layers:")
# TODO Shown top layer first. The backref is not sorted by
# `position_from_back`: this relies on SQLite returning the layers in
# insertion order, i.e. back layer first.
layers = reversed(substrate.layers)

table_content = [
    {
        'Stoichiometry': StoichioElement.to_str(lay.stoichio),
        'Thickness': ThicknessField.db_to_ui_str(lay.thickness),
        'Crystal struct.': lay.crystal_struct_str(),
    }
    for lay in layers
]
st.dataframe(DataFrame(table_content), hide_index=True, width=400)
