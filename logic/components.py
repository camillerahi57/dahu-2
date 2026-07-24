from pathlib import Path
from typing import Callable

import streamlit as st
from streamlit.navigation.page import StreamlitPage
from streamlit_dynamic_filters import DynamicFilters

from logic.page_list import pages


def browser_side_bar(dynamic_filters: DynamicFilters,
                     current_page: StreamlitPage):
    with st.sidebar:
        if st.button("Browse Libraries",
                     disabled=current_page==pages.browse_libs):
            st.switch_page(pages.browse_libs)

        if st.button("Browse Targets",
                     disabled=current_page==pages.browse_targets):
            st.switch_page(pages.browse_targets)

        if st.button("Browse Substrates",
                     disabled=current_page==pages.browse_substrates):
            st.switch_page(pages.browse_substrates)

        st.title("Filters:")
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