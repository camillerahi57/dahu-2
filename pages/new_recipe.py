"""Page for uploading a new etching recipe file (any format).

On confirm, the `Recipe` row is saved (with an `AppLog` row) and the
file is written to `user_data/`, in one transaction (a group of DB
writes that either all succeed or are all cancelled). The user is then
sent back to the recipes list.
"""
from time import sleep

import streamlit as st

from components.forms.base_classes import FileUploadForm
from components.general import init_page, switch_to_submit_successful
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Recipe
from logic.page_list import pages

init_page(pages.new_recipe)


class RecipeUploadForm(FileUploadForm):
    """File upload form that also requires a label no recipe uses."""

    def _is_coherent(self) -> tuple[bool, str]:
        """Refuse a taken label, then check the file extension.

        Etching forms pick recipes by label, hence the uniqueness. See
        `FileUploadForm._is_coherent`.
        """
        if self.label and Recipe.label_is_taken(self.label):
            return False, 'Label is already taken.'
        return super()._is_coherent()


st.header(f'New Recipe')
form = RecipeUploadForm(default_file=None)

if st.button('Confirm', disabled=not form.is_valid):
    recipe = Recipe(
        label=form.label,
        internal_file_name=Recipe.new_internal_file_name(
            form.label, form.original_file_name),
        original_file_name=form.original_file_name,
        upload_date=form.upload_date,
    )
    recipe.file_bytes = form.file_bytes
    with db.atomic():
        recipe.save()
        # Inside the transaction: if writing the file fails, the row is
        # not kept either.
        recipe.save_bytes()
    # Reason for the 0.1 s pause unknown (see DOC_NOTES.md).
    sleep(.1)
    switch_to_submit_successful(redirect_to=pages.browse_recipes)
