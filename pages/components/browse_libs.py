import streamlit as st

from logic.constants import SessionKeys as Sk

INSPECT_BUTTON_KEY = 'inspect_button'

def on_inspect_click(lib_idx_list: list[int]):
    clicked_row_idx = st.session_state[INSPECT_BUTTON_KEY]['row']
    lib_id = lib_idx_list[clicked_row_idx]
    st.session_state[Sk.SWITCH_PAGE_REQUEST_LIB_ID] = lib_id