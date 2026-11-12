"""Page for uploading a new pattern (lithography mask design) image.

Only PNG and JPEG files are accepted, since the patterns page shows
them as images. On confirm, the `Pattern` row is saved (with an
`AppLog` row) and the file is written to `user_data/`, in one
transaction (a group of DB writes that either all succeed or are all
cancelled). The user is then sent back to the patterns list.
"""
from time import sleep

import streamlit as st

from components.forms.base_classes import FileUploadForm
from components.general import init_page, switch_to_submit_successful
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Pattern
from logic.page_list import pages

init_page(pages.new_pattern)


class PatternUploadForm(FileUploadForm):
    """File upload form that also requires a label no pattern uses."""

    def _is_coherent(self) -> tuple[bool, str]:
        """Refuse a taken label, then check the file extension.

        Etching forms pick patterns by label, hence the uniqueness. See
        `FileUploadForm._is_coherent`.
        """
        if self.label and Pattern.label_is_taken(self.label):
            return False, 'Label is already taken.'
        return super()._is_coherent()


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
        # Inside the transaction: if writing the file fails, the row is
        # not kept either.
        pattern.save_bytes()
    # Reason for the 0.1 s pause unknown (see DOC_NOTES.md).
    sleep(.1)
    switch_to_submit_successful(redirect_to=pages.browse_patterns)