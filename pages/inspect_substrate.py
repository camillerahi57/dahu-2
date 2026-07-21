import streamlit as st
from pandas import DataFrame

from logic.components import inspect_page_header
from logic.constants import SUB_ID_URL_KEY
from logic.lab_modelization.db_models import Substrate, StoichioElement
from logic.page_list import pages

sub_id = st.query_params[SUB_ID_URL_KEY]
substrate: Substrate = Substrate.get_by_id(sub_id)

st.set_page_config(layout="wide", page_title=substrate.label)


def dependent_lib_error():
    libs = substrate.libraries()
    markdown = (f"The library cannot be deleted because {len(libs)} "
                f"other libraries refer to some of its characterizations:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.label}]({lib_.url})"
    st.error(markdown)


@st.dialog(title="Confirm")
def confirm_deletion_dialog():
    st.error(f"Are you sure you want to **permanently** delete the "
             f"substrate **\"{substrate.label}\"**?")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('I confirm'):
            substrate.delete_instance(recursive=True)
            st.switch_page('deleted_sub.py')


def on_delete():
    if substrate.can_be_deleted():
        confirm_deletion_dialog()
    else:
        dependent_lib_error()

inspect_page_header('Substrate', substrate.label, on_delete, lambda: None,
                    pages.browse_substrates)

st.divider()
st.subheader("Layers:")
layers = reversed(substrate.layers)

table_content = [
    {
        'Stoichiometry': StoichioElement.to_str(lay.stoichio),
        'Thickness': lay.thickness,  # TODO add unit.
        'Crystal struct.': lay.crystal_struct_str(),
    }
    for lay in layers
]
st.dataframe(DataFrame(table_content), hide_index=True, width=400)
