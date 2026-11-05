"""UI pieces shared by the browsing pages (libraries, targets,
substrates, patterns, recipes): the sidebar, the "Inspect" button column
and the rows of the file lists.
"""
import streamlit as st
from streamlit.navigation.page import StreamlitPage
from streamlit_dynamic_filters import DynamicFilters

from components.general import show_html_link
from logic.constants import SessionKeys as Sk
from logic.lab_modelization.db_models import UserUploadedFile, Pattern


def browser_side_bar(dynamic_filters: DynamicFilters|None,
                     current_page: StreamlitPage):
    """Draw the sidebar: links to the browsing pages, then the filters.

    Replaces Streamlit's built-in page navigation, which is turned off.
    The current page is shown in bold instead of as a link.

    Args:
        dynamic_filters: Filter widgets of the page's table, drawn below
            the links. None on pages without a table.
        current_page: The page being drawn.
    """
    from logic.page_list import pages
    sidebar_pages = [
        pages.browse_libs,
        pages.browse_targets,
        pages.browse_substrates,
        pages.browse_patterns,
        pages.browse_recipes,
        pages.admin,
    ]
    with st.sidebar:
        for page in sidebar_pages:
            if page == current_page:
                with st.container(border=True, width='content'):
                    st.write(f'**{page.title}**')
            else:
                show_html_link(page.title, page,
                               border=False if page == pages.admin else True)

        if dynamic_filters is not None:
            st.title("Filters:")
    if dynamic_filters is not None:
        dynamic_filters.display_filters(location='sidebar')


# Widget key of the button column of a table: "Inspect" on the browsing
# pages, "Details" in the layer table of the inspect library page. After
# a click, Streamlit stores the clicked row under this key in the session
# state (the per-tab dictionary that survives reruns), as a dictionary
# whose `'row'` item is the index of the clicked row.
INSPECT_BUTTON_KEY = 'inspect_button'


def on_inspect_click(object_idx_list: list[int]):
    """Remember which object's "Inspect" button was clicked.

    Callback (a function Streamlit calls when a widget is used, before
    rerunning the page) of the "Inspect" column on the browsing pages.
    The page then sees `Sk.INSPECT_OBJ_ID` in the session state and
    switches to the inspect page of that object.

    Side effect: writes `Sk.INSPECT_OBJ_ID` in the session state.

    Args:
        object_idx_list: DB ids of the objects, in the same order as the
            rows of the table.
    """
    clicked_row_idx = st.session_state[INSPECT_BUTTON_KEY]['row']
    obj_id = object_idx_list[clicked_row_idx]
    st.session_state[Sk.INSPECT_OBJ_ID] = obj_id


def file_row(file: UserUploadedFile):
    """Draw one file of the patterns or recipes list, with its buttons.

    Buttons: download, show (patterns only), rename and delete. The
    last three open dialogs (pop-up windows) defined in the
    `browse_patterns` page.

    Args:
        file: A `Pattern` or a `Recipe`.
    """
    # TODO Import from a page, which causes a page load.
    from browse_patterns import (
        show_pattern, show_rename_dialog, show_delete_dialog)
    with st.container(
            border=True, horizontal=True, vertical_alignment='center',
            width='content'):
        # `file_bytes` is None when the file is missing from `user_data/`.
        if not file.file_bytes:
            st.write('File could not be found.')
        else:
            st.download_button('', file.file_bytes, file.download_file_name,
                               icon=':material/download:',
                               key=f'download_{file.id}')
        if isinstance(file, Pattern):
            if st.button('Show', key=f'show_{file.id}'):
                show_pattern(file)
        with st.container(width=300):
            st.write(f'**{file.label}**')
        if st.button('✏️ Rename', key=f'rename_{file.id}'):
            show_rename_dialog(file)
        if st.button('❌ Delete', key=f'delete_{file.id}'):
            show_delete_dialog(file)
