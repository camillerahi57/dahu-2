"""The "Uploaded Files" box of the inspect library page: the list of a
library's files, with download and delete buttons, and an Add button.
"""
import streamlit as st

from components.general import switch_page_bttn, icon
from logic.constants import IdType
from logic.lab_modelization.db_models import LibraryFile, Library
from logic.page_list import pages


def file_list_item(uploaded: LibraryFile, key: int):
    """Draw one file of the list: download button, label, Delete button.

    If the file is missing from `user_data/`, "_File missing_" is shown
    instead of the download button: `file_bytes` is then None, which
    `st.download_button` refuses (it would crash the whole page).

    Args:
        uploaded: The file.
        key: Makes the widget keys (the names Streamlit uses to tell
            widgets apart) unique; the callers pass the file's id.
    """
    with st.container(horizontal=True, vertical_alignment='center',
                      border=True):
        file_bytes = uploaded.file_bytes
        if file_bytes is None:
            st.write('_File missing_')
        else:
            st.download_button(
                label='Download',
                data=file_bytes,
                file_name=uploaded.download_file_name,
                icon=':material/download:',
                key=f'download_bttn_{key}',
            )
        st.write(uploaded.label)
        with st.container(horizontal_alignment='right'):
            if st.button('Delete ❌', key=f'del_bttn_{key}'):
                delete_dialog(uploaded)



@st.dialog('Delete?')
def delete_dialog(uploaded: LibraryFile):
    """Ask for confirmation, then delete a library file.

    Opens as a dialog (pop-up window). On confirmation, deletes the row
    and the stored file, then reruns the page (re-executes its script)
    to refresh the list.

    Side effects: DB delete, which writes an `AppLog` row; deletes the
    file from `user_data/`.

    Args:
        uploaded: The file to delete.
    """
    st.error(f"Are you sure you want to **permanently** delete "
             f"**{uploaded.label}**?")
    if st.button('Confirm'):
        uploaded.delete_with_parts()
        st.rerun()

def file_list_container(files: list[LibraryFile], lib: Library):
    """Draw the "Uploaded Files" box of a library.

    Args:
        files: The library's files.
        lib: The library, for the Add button's link to the upload page.
    """
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

