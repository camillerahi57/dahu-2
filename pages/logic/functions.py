import re
from pathlib import Path
from time import sleep
import streamlit as st

from streamlit.runtime.state import SessionStateProxy
from streamlit_cookies_controller import CookieController

from logic.constants import StorageKeys, PAGE_NAME_KEY


def highlight_rows(row) -> list[str]:
    if row.target_name % 2 == 0:
        return ['background-color: white'] * len(row)
    else:
        return ['background-color: #f0f0f0'] * len(row)


def letter_count(text: str) -> int:
    upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return len(''.join(i for i in text if i.upper() in upper))


def new_controller() -> CookieController:
    controller = CookieController()  # It takes time to get it loaded.
    waited = 0
    while not controller.get('cookie_ready'):
        # In case it's the first time and the key has never been set:
        controller.set('cookie_ready', True)
        # In case the key has been set, but we have to wait:
        sleep(0.1)
        waited += 0.1
        if waited > 5:
            raise RuntimeError('Not able to load cookie')
    return controller


def load_session_state(page_name: str|Path) -> SessionStateProxy:
    sess = st.session_state
    update_from_cookies(sess)
    sess[PAGE_NAME_KEY] = page_name
    return sess


def update_from_cookies(sess: SessionStateProxy):
    controller = new_controller()
    for key in StorageKeys:
        stored_value = controller.get(key)
        if stored_value is not None:
            sess[key] = stored_value


def save_session_state(sess: SessionStateProxy):
    controller = new_controller()
    for key in StorageKeys:
        if key in sess.keys():
            controller.set(key, sess[key])


def email_user_name(email_address: str) -> str:
    return re.match(r'[^@]+', email_address)[0]