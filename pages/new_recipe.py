from time import sleep

import streamlit as st

from components.forms.base_classes import FileUploadForm
from components.streamlit_tools import init_page, switch_to_submit_successful
from logic.lab_modelization.db_models import db, Recipe
from logic.page_list import pages

init_page(pages.new_recipe)


class RecipeUploadForm(FileUploadForm):
    def _is_coherent(self) -> tuple[bool, str]:
        if self.label and Recipe.label_is_taken(self.label):
            return False, 'Label is already taken.'
        return True, ''


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
        recipe.save_bytes()
    sleep(.1)
    switch_to_submit_successful(redirect_to=pages.browse_recipes)
