import streamlit as st

from logic.constants import SessionKeys as Sk

INSPECT_BUTTON_KEY = 'inspect_button'

def on_inspect_click(object_idx_list: list[int]):
    clicked_row_idx = st.session_state[INSPECT_BUTTON_KEY]['row']
    obj_id = object_idx_list[clicked_row_idx]
    st.session_state[Sk.INSPECT_OBJ_ID] = obj_id
