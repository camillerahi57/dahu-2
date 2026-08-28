import streamlit as st
from streamlit.navigation.page import StreamlitPage
from streamlit_dynamic_filters import DynamicFilters

from components.general import show_html_link
from logic.constants import SessionKeys as Sk
from logic.page_list import pages


def browser_side_bar(dynamic_filters: DynamicFilters|None,
                     current_page: StreamlitPage):
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
