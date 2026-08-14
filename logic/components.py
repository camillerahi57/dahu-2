from typing import Callable

import streamlit as st
from streamlit.navigation.page import StreamlitPage
from streamlit_dynamic_filters import DynamicFilters

from logic.functions import show_html_link
from logic.page_list import pages


def browser_side_bar(dynamic_filters: DynamicFilters|None,
                     current_page: StreamlitPage):
    titles_and_pages = [
        ("Browse Libraries", pages.browse_libs),
        ("Browse Targets", pages.browse_targets),
        ("Browse Substrates", pages.browse_substrates),
        ("Browse Patterns", pages.browse_patterns),
        ("Browse Recipes", pages.browse_recipes),
    ]
    with st.sidebar:
        for title, page in titles_and_pages:
            if page == current_page:
                with st.container(border=True, width='content'):
                    st.write(f'**{title}**')
            else:
                show_html_link(title, page, border=True)
        # if st.button("Browse Libraries",
        #              disabled=current_page==pages.browse_libs,
        #              key='side_bar_libs'):
        #     st.switch_page(pages.browse_libs)
        #
        # if st.button("Browse Targets",
        #              disabled=current_page==pages.browse_targets,
        #              key='side_bar_targets'):
        #     st.switch_page(pages.browse_targets)
        #
        # if st.button("Browse Substrates",
        #              disabled=current_page==pages.browse_substrates,
        #              key='side_bar_subs'):
        #     st.switch_page(pages.browse_substrates)
        #
        # if st.button("Browse Patterns",
        #              disabled=current_page==pages.browse_patterns,
        #              key='side_bar_patts'):
        #     st.switch_page(pages.browse_patterns)
        #
        # if st.button("Browse Recipes",
        #              disabled=current_page==pages.browse_recipes,
        #              key='side_bar_recips'):
        #     st.switch_page(pages.browse_recipes)

        if dynamic_filters is not None:
            st.title("Filters:")
    if dynamic_filters is not None:
        dynamic_filters.display_filters(location='sidebar')


def inspect_page_header(object_type: str, instance_name: str,
                        on_delete: Callable, on_edit: Callable = None):
    col1, col2 = st.columns(2)
    with col1:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.write(f'**{object_type.upper()}**')
            st.subheader(instance_name)
    with col2:
        with st.container(horizontal=True, horizontal_alignment='right'):
            if on_edit is not None:
                if st.button('Edit ✏️'):
                    on_edit()
            if st.button(f'Delete {object_type} ❌'):
                on_delete()