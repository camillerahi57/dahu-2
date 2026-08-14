from time import sleep

import streamlit as st

from components.forms.base_classes import FileUploadForm
from components.streamlit_tools import init_page, switch_to_submit_successful
from logic.lab_modelization.db_models import db, Pattern
from logic.page_list import pages

init_page(pages.new_pattern)


class PatternUploadForm(FileUploadForm):
    def _is_coherent(self) -> tuple[bool, str]:
        if self.label and Pattern.label_is_taken(self.label):
            return False, 'Label is already taken.'
        return True, ''


st.header(f'New Pattern')
form = PatternUploadForm(default_file=None,
                         accepted_formats=['png', 'jpg', 'jpeg'])

if st.button('Confirm', disabled=not form.is_valid):
    uploaded = form.to_user_upload()
    pattern = Pattern(
        label=uploaded.label,
        file_name=uploaded.file_name,
        upload_date=uploaded.upload_date,
    )
    pattern.file_bytes = uploaded.file_bytes
    with db.atomic():
        pattern.save()
        pattern.save_bytes()
    sleep(.1)
    switch_to_submit_successful(redirect_to=pages.browse_patterns)