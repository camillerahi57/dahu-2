import streamlit as st
from pandas import DataFrame

from logic.components import inspect_page_header
from logic.constants import SUB_ID_URL_KEY
from logic.db_schema import Substrate

sub_id = st.query_params[SUB_ID_URL_KEY]
substrate: Substrate = Substrate.get_by_id(sub_id)

st.set_page_config(layout="wide", page_title=substrate.name)


def dependent_lib_error():
    libs = substrate.libraries()
    markdown = (f"The library cannot be deleted because {len(libs)} "
                f"other libraries refer to some of its characterizations:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.name}]({lib_.get_url()})"
    st.error(markdown)


@st.dialog(title="Confirm")
def confirm_deletion_dialog():
    st.error(f"Are you sure you want to **permanently** delete the "
             f"substrate **\"{substrate.name}\"**?")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('I confirm'):
            substrate.delete_instance()
            st.switch_page('deleted_sub.py')


def on_delete():
    if substrate.can_be_deleted():
        confirm_deletion_dialog()
    else:
        dependent_lib_error()

inspect_page_header('Substrate', substrate.name, on_delete, lambda: None,
                    'browse_substrates.py')

st.divider()
st.subheader("Layers:")
st.markdown("_Top of the film to the bottom_")
layers = reversed(substrate.layers)

table_content = [
    {
        'Stoichiometry': lay.stoichiometry,
        'Thickness': lay.thickness,  # TODO add unit.
        'Crystal struct.': lay.crystal_struct_str(),
    }
    for lay in layers
]
st.dataframe(DataFrame(table_content), hide_index=True, width=400)
