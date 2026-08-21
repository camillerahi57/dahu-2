import os
import re
import secrets
from time import sleep
from urllib import parse

from streamlit_cookies_controller import CookieController

from components.general import sess
from logic.constants import CookieKeys as Ck, SessionKeys as Sk


def letter_count(text: str) -> int:
    upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return len(''.join(i for i in text if i.upper() in upper))

def new_controller() -> CookieController:
    if 'cookie_controller' in sess:
        return sess['cookie_controller']

    controller = CookieController()
    waited = 0
    while not controller.get('cookie_ready'):
        controller.set('cookie_ready', True)
        sleep(0.1)
        waited += 0.1
        if waited > 5:
            raise RuntimeError('Not able to load cookie')

    sess['cookie_controller'] = controller
    return controller

# def new_controller() -> CookieController:
#     controller = CookieController()  # It takes time to get it loaded.
#     waited = 0
#     while not controller.get('cookie_ready'):
#         # In case it's the first time and the key has never been set:
#         controller.set('cookie_ready', True)
#         # In case the key has been set, but we have to wait:
#         sleep(0.1)
#         waited += 0.1
#         if waited > 5:
#             raise RuntimeError('Not able to load cookie')
#     return controller


def add_cookie_data_to_session():
    controller = new_controller()
    for key in Ck:
        stored_value = controller.get(key)
        if stored_value is not None:
            sess[key] = stored_value


def reset_session():
    for key in sess:
        if key in Sk:
            del sess[key]


def save_cookies():
    controller = new_controller()
    for key in Ck:
        if key in sess:
            controller.set(key, sess[key])


def get_email_user_name(email_address: str) -> str:
    return re.match(r'[^@]+', email_address)[0]


def is_valid_email_address(email_address: str) -> bool:
    # From https://stackoverflow.com/a/201378:
    email_regex = r"(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"  # noqa Long line.
    match = re.fullmatch(email_regex, email_address)
    return match is not None


def get_file_extension(file_name: str):
    return os.path.splitext(file_name)[1].removeprefix('.')


def q_param_str(q_params: dict[str, str|int], include_question_mark=False):
    q_params = q_params or {}
    for k, v in q_params.items():
        # If there are numbers, converts them to strings:
        q_params[k] = str(v)
    string = parse.urlencode(q_params)
    if include_question_mark:
        string = '?' + string
    return string


def to_ascii(str_: str):
    return str_.encode(  # To bytes.
        'ascii', 'xmlcharrefreplace'
    ).decode('ascii')  # Back to string.


def remove_digits(s: str) -> str:
    return ''.join([c for c in s if not c.isdigit()])


def rand_str(length=21) -> str:
    """Generates a random string of upper/lowercase letters and digits."""
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
