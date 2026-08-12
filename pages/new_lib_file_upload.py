from time import sleep

import streamlit as st

from components.forms.base_classes import FileUploadForm
from components.streamlit_tools import init_page, current_params, \
    switch_to_submit_successful
from logic.constants import IdType
from logic.lab_modelization.db_models import db, Library, GeneralLibraryFile
from logic.page_list import pages

init_page(pages.new_lib_file_upload)
lib_id = current_params()[IdType.LIB]
lib: Library = Library.get_by_id(lib_id)


st.header(f'New File for {lib.label}')
form = FileUploadForm(default_file=None)
if st.button('Confirm', disabled=not form.is_valid):
    uploaded = form.to_user_upload()
    lib_file = GeneralLibraryFile(
        label=uploaded.label,
        file_name=uploaded.file_name,
        upload_date=uploaded.upload_date,
        library=lib,
    )
    lib_file.file_bytes = uploaded.file_bytes
    with db.atomic():
        lib_file.save()
        lib_file.save_bytes()
    sleep(.1)
    switch_to_submit_successful()