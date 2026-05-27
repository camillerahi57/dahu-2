from pathlib import Path
from typing import Callable

import streamlit as st
from streamlit_dynamic_filters import DynamicFilters


def browser_side_bar(dynamic_filters: DynamicFilters, current_page: str | Path):
    with st.sidebar:
        if st.button("Browse Libraries",
                     disabled=current_page=='browse_libs.py'):
            st.switch_page('browse_libs.py')

        if st.button("Browse Targets",
                     disabled=current_page=='browse_targets.py'):
            st.switch_page('browse_targets.py')

        if st.button("Browse Substrates",
                     disabled=current_page=='browse_substrates.py'):
            st.switch_page('browse_substrates.py')

        st.title("Filters:")
    dynamic_filters.display_filters(location='sidebar')


def inspect_page_header(object_type: str, instance_name: str,
                        on_delete: Callable, on_edit: Callable,
                        browse_page: str):
    if st.button('← Browse'):
        st.switch_page(browse_page)
    col1, col2 = st.columns(2)
    with col1:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.write(f'**{object_type.upper()}**')
            st.subheader(instance_name)
    with col2:
        with st.container(horizontal=True, horizontal_alignment='right'):
            if st.button('Edit ✏️'):
                on_edit()
            if st.button(f'Delete {object_type.lower()} ❌'):
                on_delete()