import streamlit as st

from components.general import switch_page_bttn, icon
from logic.constants import IdType
from logic.lab_modelization.db_models import LibraryFile, Library
from logic.page_list import pages


def file_list_item(uploaded: LibraryFile, key: int):
    with st.container(horizontal=True, vertical_alignment='center',
                      border=True):
        st.download_button(
            label='Download',
            data=uploaded.file_bytes,
            file_name=uploaded.download_file_name,
            icon=':material/download:',
            key=f'download_bttn_{key}',
        )
        if uploaded.is_a_charac_file:
            charac_type = uploaded.charac.type_
            st.write(f"{uploaded.label} · 📊 _{charac_type} measurement_")
        else:
            st.write(uploaded.label)
        with st.container(horizontal_alignment='right'):
            if st.button('Delete ❌', key=f'del_bttn_{key}'):
                delete_dialog(uploaded)



@st.dialog('Delete?')
def delete_dialog(uploaded: LibraryFile):
    st.error(f"Are you sure you want to **permanently** delete "
             f"**{uploaded.label}**?")
    if st.button('Confirm'):
        uploaded.delete_with_parts()
        st.rerun()

def file_list_container(files: list[LibraryFile], lib: Library):
    with st.container(border=True):
        st.subheader('Uploaded Files:')
        if not files:
            st.write('_No file uploaded yet._')
        for file in files:
            file_list_item(file, key=file.id)

        switch_page_bttn(
            pages.new_lib_file_upload,
            label='Add',
            q_params={IdType.LIB: lib.id},
            icon_=icon('add_2')
        )

