"""Page listing the uploaded pattern files (lithography mask designs).

Each file is drawn by `file_row` with download, show, rename and delete
buttons.

This module also defines the show, rename and delete dialogs (pop-up
windows) that `file_row` opens, for both patterns and recipes.
`file_row` imports them from here, which runs this page a second time
inside the calling page (see the TODO in `file_row` and DOC_NOTES.md).
"""
from time import sleep
from typing import Iterable

import streamlit as st

from components.browsing import file_row
from components.general import init_page, show_html_link
from logic.constants import IdType
from logic.lab_modelization.db_models import (
    Pattern, UserUploadedFile, Recipe, Etching)
from logic.page_list import pages

init_page(pages.browse_patterns, show_home_btn=False)

def body():
    """Draw the sidebar, the "Add a new pattern" link and the files."""
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
    """Show a pattern file as an image in a dialog.

    Args:
        pattern: The pattern to show.
    """
    # A width larger than any screen, meant to make the image fill the
    # dialog's width.
    st.image(pattern.file_bytes, width=99999)


@st.dialog('Delete?')
def show_delete_dialog(file: UserUploadedFile):
    """Delete a pattern or recipe after confirmation, if it is unused.

    A file used by etchings cannot be deleted (their foreign keys, i.e.
    columns holding the id of a row of another table, are declared
    `on_delete='RESTRICT'`); the dialog then links to the libraries of
    those etchings instead.

    Side effects on confirm: deletes the row and the stored file in
    `user_data/` (see `delete_with_parts`), writes an `AppLog` row, and
    reruns the page.

    Args:
        file: A `Pattern` or a `Recipe`.
    """
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
            # Reason for the 0.1 s pause unknown (see DOC_NOTES.md).
            sleep(.1)
            st.rerun()


@st.dialog('Rename')
def show_rename_dialog(file: UserUploadedFile):
    """Change the label of a pattern or recipe.

    Confirm stays disabled while the new label is empty or already used
    by a file of the same kind, hence also while it is unchanged.

    Side effects on confirm: saves the row, writes an `AppLog` row, and
    reruns the page.

    Args:
        file: A `Pattern` or a `Recipe`.
    """
    new_label = st.text_input('New label:', file.label) or ''
    file_type = file.__class__
    is_valid = bool(new_label) and not file_type.label_is_taken(new_label)

    if st.button('Confirm', disabled=not is_valid):
        file.label = new_label
        file.save()
        # Reason for the 0.1 s pause unknown (see DOC_NOTES.md).
        sleep(.1)
        st.rerun()


body()