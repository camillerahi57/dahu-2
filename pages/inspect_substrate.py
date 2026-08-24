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
    libs = substrate.libraries()
    markdown = (f"The library cannot be deleted because {len(libs)} "
                f"other librarie(s) refer to some of its characterizations:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.label}]({lib_.url})"
    st.error(markdown)


@st.dialog(title="Confirm")
def confirm_deletion_dialog():
    st.error(f"Are you sure you want to **permanently** delete the "
             f"substrate **\"{substrate.label}\"**?")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('I confirm'):
            substrate.delete_with_parts()
            switch_to_submit_successful(redirect_to=pages.browse_substrates)


def on_delete():
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
