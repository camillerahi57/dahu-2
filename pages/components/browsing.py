import streamlit as st
from streamlit.navigation.page import StreamlitPage
from streamlit_dynamic_filters import DynamicFilters

from components.general import show_html_link
from logic.constants import SessionKeys as Sk
from logic.lab_modelization.db_models import UserUploadedFile, Pattern


def browser_side_bar(dynamic_filters: DynamicFilters|None,
                     current_page: StreamlitPage):
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


INSPECT_BUTTON_KEY = 'inspect_button'


def on_inspect_click(object_idx_list: list[int]):
    clicked_row_idx = st.session_state[INSPECT_BUTTON_KEY]['row']
    obj_id = object_idx_list[clicked_row_idx]
    st.session_state[Sk.INSPECT_OBJ_ID] = obj_id


def file_row(file: UserUploadedFile):
    from browse_patterns import show_pattern, show_rename_dialog, show_delete_dialog
    with st.container(
            border=True, horizontal=True, vertical_alignment='center',
            width='content'):
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
