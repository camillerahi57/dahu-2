from typing import Literal
from urllib import parse

import keyboard
import streamlit as st
from streamlit.navigation.page import StreamlitPage

from logic.constants import (
    SessionKeys as Sk, REDIRECT_PATH, RESOURCE_TYPE, OBJ_ID,
    IdType
)
from logic.page_list import pages

sess = st.session_state  # Shorthand.


def init_page(page: StreamlitPage, show_home_btn = True):
    from logic.functions import reset_session, add_cookie_data_to_session
    if show_home_btn:
        switch_page_bttn(pages.browse_libs, label='Home', icon='🏠')
    page_changed = sess.get(Sk.CURRENT_PATH) != page.url_path
    if page_changed:
        reset_session()
        sess[Sk.CURRENT_PATH] = page.url_path
    add_cookie_data_to_session()


def current_params() -> dict[str, str]:
    return st.query_params.to_dict()


def switch_to_submit_successful(
        redirect_to: StreamlitPage = None, id_type: IdType = None,
        object_id: int = None):
    from logic.page_list import pages

    params = {}
    if redirect_to:
        params[REDIRECT_PATH] = redirect_to.url_path
    if object_id:  # Provide redirection to a specific object page.
        params[RESOURCE_TYPE] = id_type
        params[OBJ_ID] = str(object_id)

    st.switch_page(pages.submission_successful, query_params=params)


def switch_page_bttn(
        page: StreamlitPage | str, *, label: str,
        q_params: dict[str, str|int] = None, key: str = None,
        type_: Literal["primary", "secondary", "tertiary"] = 'secondary',
        icon: str = None):
    """Don't use st.switch_page to go from current page P1 to another page P2 if
    P1 has query parameters in its URL. The browser's back button
    will not restore these parameters if the user wants to go back. This will
    break navigation.

    To solve his, use an HTML link instead. This alternative is chosen
    automatically if you use the present function."""

    if isinstance(page, str):
        page = pages.from_url_path(page)

    q_params = q_params or {}
    convert_values_to_str(q_params)

    if not key:
        key = to_ascii(label)  # Create a key from label.

    # If there currently are q_parameters:
    if len(current_params()) > 0:
        from logic.functions import show_html_link
        show_html_link(label, page, border=True, icon=icon, q_params=q_params)
    else:
        if st.button(f'{icon} {label}', key=key, type=type_):
            st.switch_page(page, query_params=q_params)


def convert_values_to_str(dict_: dict):
    for k, v in dict_.items():
        dict_[k] = str(v)


def to_ascii(str_: str):
    return str_.encode(  # To bytes.
        'ascii', 'xmlcharrefreplace'
    ).decode('ascii')  # Back to string.


def close_button(label: str = "Close"):
    if st.button(label):
        keyboard.press_and_release('ctrl+w')
