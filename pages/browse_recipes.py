"""Page listing the uploaded etching recipe files.

Each file is drawn by `file_row` with download, rename and delete
buttons; the rename and delete dialogs are defined in
`browse_patterns.py`.
"""
from typing import Iterable

import streamlit as st

from components.browsing import browser_side_bar, file_row
from components.general import init_page, show_html_link
from logic.lab_modelization.db_models import Recipe
from logic.page_list import pages

init_page(pages.browse_recipes, show_home_btn=False)
browser_side_bar(None, pages.browse_recipes)

def body():
    """Draw the "Add a new recipe" link and the list of recipe files."""
    st.set_page_config(layout="wide")
    show_html_link("Add a new recipe", pages.new_recipe, border=True,
                   icon_="➕")
    recipes: Iterable[Recipe] = Recipe.select()
    for r in recipes:
        file_row(r)

body()