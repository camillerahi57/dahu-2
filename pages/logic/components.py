from pathlib import Path

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


