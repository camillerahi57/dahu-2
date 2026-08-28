from typing import Iterable

import streamlit as st

from browse_patterns import file_row
from components.browsing import browser_side_bar
from components.general import init_page, show_html_link
from logic.lab_modelization.db_models import Recipe
from logic.page_list import pages

init_page(pages.browse_recipes, show_home_btn=False)
browser_side_bar(None, pages.browse_recipes)

def body():
    st.set_page_config(layout="wide")
    show_html_link("Add a new recipe", pages.new_recipe, border=True,
                   icon_="➕")
    recipes: Iterable[Recipe] = Recipe.select()
    for r in recipes:
        file_row(r)

# On vient de finir une feature et de la commit. Prochaine feature:
# Ajouter des champs dans UserUploaded ?

body()