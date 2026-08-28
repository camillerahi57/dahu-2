from time import sleep

import streamlit as st

from components.forms.base_classes import FileUploadForm
from components.general import init_page, switch_to_submit_successful
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Pattern
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
    pattern = Pattern(
        label=form.label,
        internal_file_name=Pattern.new_internal_file_name(
            form.label, form.original_file_name),
        original_file_name=form.original_file_name,
        upload_date=form.upload_date,
    )
    pattern.file_bytes = form.file_bytes
    with db.atomic():
        pattern.save()
        pattern.save_bytes()
    sleep(.1)
    switch_to_submit_successful(redirect_to=pages.browse_patterns)