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


# # class CookieLoader:
# #     """Usage: to get a cookie, create a loader and call get_cookie on it. BUT this
# #      is not optimal. The best way is to create a loader as early as possible in the file
# #      (the loading starts), and then, when the cookie is needed, call get_cookie. That
# #      way the cookie has already been loaded and is available instantly."""
# #     def __init__(self):
# #         self.cookie = CookieController()
# #
# #     def get_cookie(self):
# #         while True:
# #             if self.cookie.get('cookie_ready'):
# #                 return self.cookie
# #             else:
# #                 # In case it's the first time and the key has never been set:
# #                 self.cookie.set('cookie_ready', True)
# #                 # In case the key has been set, but we have to wait:
# #                 sleep(0.1)
#
#
# # class Cookie:
# #     def __init__(self):
# #         controller = CookieController()
# #         while not controller.get('cookie_ready'):
# #             # In case it's the first time and the key has never been set:
# #             controller.set('cookie_ready', True)
# #             # In case the key has been set, but we have to wait:
# #             sleep(0.1)
# #
# #         self.controller = controller
# #         self.lib_filters: list = None
#
#
# @dataclass
# class Cookie:
#     controller: CookieController|None  # For loading and saving the cookie.
#     used_constructor: bool = False  # To warn if cookie created outside the 'load' method.
#
#     last_email_used: str|None = None
#     lib_filters: dict|None = None
#     target_filters: dict|None = None
#
#     def __post_init__(self):
#         if not self.used_constructor:
#             raise RuntimeError("Please create a new instance of a cookie only using the "
#                                "'load' method.")
#
#     def save(self, sess: SessionStateProxy):
#         sess[cookie_data_key] = self  # Saved in Streamlit session (faster retrieval).
#         self_copy = deepcopy(self)
#         self_copy.controller = None
#         self.controller.set(cookie_data_key, asdict(self_copy))  # Saved in storage (if browser is closed).
#
#     @classmethod
#     def load(cls, sess: SessionStateProxy) -> Cookie:
#         # Try to get cookie from session state (fastest retrieval):
#         cookie = sess.get(cookie_data_key)
#         if cookie is None:  # If it failed, get it from browser storage:
#             controller = cls.new_controller()
#             cookie = cls._load_from_storage(controller)
#             if cookie is None:  # If it failed, create a fresh one:
#                 cookie = cls(controller=controller, used_constructor=True)
#         return cookie
#
#     @staticmethod
#     def new_controller() -> CookieController:
#         controller = CookieController()  # It takes time to get it loaded.
#         waited = 0
#         while not controller.get('cookie_ready'):
#             # In case it's the first time and the key has never been set:
#             controller.set('cookie_ready', True)
#             # In case the key has been set, but we have to wait:
#             sleep(0.1)
#             waited += 0.1
#             if waited > 5:
#                 raise RuntimeError('Not able to load cookie')
#         return controller
#
#     @classmethod
#     def _load_from_storage(cls, controller: CookieController) -> Cookie|None:
#         cookie_dict = controller.get(cookie_data_key)
#         if cookie_dict is None:
#             return None
#         else:
#             cookie = cls(**cookie_dict)
#             # Put the newly created controller (for saving later):
#             cookie.controller = controller
#             return cookie


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


