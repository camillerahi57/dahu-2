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
        switch_page_bttn(pages.browse_libs, label='🏠 Home', force_same_tab=True)
    page_paged = sess.get(Sk.CURRENT_PATH) != page.url_path
    if page_paged:
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
        force_same_tab: bool = False):
    """Don't use st.switch_page to go from current page P1 to another page P2 if
    P1 has query parameters in its URL. The browser's back button
    will not restore these parameters if the user wants to go back. This will
    break navigation.

    In this case, use st.page_link, which will open the page
    in a new tab. That way, if the user wants to go back, they will simply close
    the newly opened tab. Not ideal but there is no satisfying alternative."""

    if isinstance(page, str):
        page = pages.from_url_path(page)

    q_params = q_params or {}
    for k, v in q_params.items():
        # If there are numbers, converts them to strings:
        q_params[k] = str(v)

    if key is None:
        key = label.encode(  # To bytes.
            'ascii', 'xmlcharrefreplace'
        ).decode('ascii')  # Back to string.

    url = page.url_path + '?' + parse.urlencode(q_params)

    # If there currently are q_parameters:
    if len(current_params()) > 0 and not force_same_tab:
        st.link_button(label, url, key=key, type=type_)  # Open in new tab.
    else:
        if st.button(label, key=key, type=type_):
            # Open in same tab:
            st.switch_page(page, query_params=q_params)


def close_button(label: str = "Close"):
    if st.button(label):
        keyboard.press_and_release('ctrl+w')
