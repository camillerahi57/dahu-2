from time import sleep
from typing import Iterable

import streamlit as st

from components.browsing import file_row
from components.general import init_page, show_html_link
from logic.constants import IdType
from logic.lab_modelization.db_models import Pattern, UserUploadedFile, Recipe,\
    Etching
from logic.page_list import pages

init_page(pages.browse_patterns, show_home_btn=False)

def body():
    from components.browsing import browser_side_bar
    browser_side_bar(None, pages.browse_patterns)

    st.set_page_config(layout="wide")

    show_html_link("Add a new pattern", pages.new_pattern, border=True,
                   icon_="➕")

    patterns: Iterable[Pattern] = Pattern.select()

    for pattern in patterns:
        file_row(pattern)


@st.dialog('Pattern')
def show_pattern(pattern: Pattern):
    st.image(pattern.file_bytes, width=99999)


@st.dialog('Delete?')
def show_delete_dialog(file: UserUploadedFile):
    used_by: list[Etching] = []
    if isinstance(file, Pattern):
        used_by = list(file.etchings)
    if isinstance(file, Recipe):
        used_by = list(file.etchings)
    if used_by:
        st.error("Cannot delete because it is used in:")
        for etch in used_by:
            lib = etch.film_modif.film.library
            show_html_link(
                label=lib.label,
                page=pages.inspect_lib,
                q_params={IdType.LIB: lib.id}
            )
    else:
        st.error(f"Are you sure you want **permanently** delete {file.label}?")
        if st.button('Confirm'):
            file.delete_with_parts()
            sleep(.1)
            st.rerun()


@st.dialog('Rename')
def show_rename_dialog(file: UserUploadedFile):
    new_label = st.text_input('New label:', file.label)
    file_type = file.__class__
    is_valid = bool(new_label) and not file_type.label_is_taken(new_label)
    if st.button('Confirm', disabled=not is_valid):
        file.label = new_label
        file.save()
        sleep(.1)
        st.rerun()


body()