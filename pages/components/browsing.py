import streamlit as st
from streamlit.navigation.page import StreamlitPage
from streamlit_dynamic_filters import DynamicFilters

from components.general import show_html_link
from logic.constants import SessionKeys as Sk
from logic.page_list import pages


def browser_side_bar(dynamic_filters: DynamicFilters|None,
                     current_page: StreamlitPage):
    title_page_has_border = [
        ("Browse Libraries", pages.browse_libs, True),
        ("Browse Targets", pages.browse_targets, True),
        ("Browse Substrates", pages.browse_substrates, True),
        ("Browse Patterns", pages.browse_patterns, True),
        ("Browse Recipes", pages.browse_recipes, True),
        ("Incident", pages.restore_app_state, False),
    ]
    with st.sidebar:
        for title, page, has_border in title_page_has_border:
            if page == current_page:
                with st.container(border=True, width='content'):
                    st.write(f'**{title}**')
            else:
                show_html_link(title, page, border=has_border)

        if dynamic_filters is not None:
            st.title("Filters:")
    if dynamic_filters is not None:
        dynamic_filters.display_filters(location='sidebar')


INSPECT_BUTTON_KEY = 'inspect_button'


def on_inspect_click(object_idx_list: list[int]):
    clicked_row_idx = st.session_state[INSPECT_BUTTON_KEY]['row']
    obj_id = object_idx_list[clicked_row_idx]
    st.session_state[Sk.INSPECT_OBJ_ID] = obj_id
