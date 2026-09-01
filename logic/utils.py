import io
import os
import re
import secrets
from sqlite3 import OperationalError
from time import sleep
from typing import Any, Iterable
from urllib import parse

import pandas as pd
from streamlit_cookies_controller import CookieController

from logic.constants import SessionKeys as Sk, CookieKeys
from logic.lab_modelization.base_classes import Event
from logic.lab_modelization.db_enums import EventType, LogSeverity
from logic.lab_modelization.db_models import dahu_2_models, AppLog, \
    DeteriorationState, FilmModification, Film, Target


def letter_count(text: str) -> int:
    upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return len(''.join(i for i in text if i.upper() in upper))

def new_controller() -> CookieController:
    from logic.global_variables import sess
    if 'cookie_controller' in sess:
        return sess['cookie_controller']

    controller = CookieController()
    waited = 0
    while not controller.get('cookie_ready'):
        controller.set('cookie_ready', True)
        sleep(0.1)
        waited += 0.1
        if waited > 5:
            event = Event(
                type=EventType.UI_ERROR,
                notify=False,
                severity=LogSeverity.WARNING,
                description="Cookie feature in user interface is not working "
                            "properly. Cookie could not be loaded.",
            )
            AppLog.save_new(event)

    sess['cookie_controller'] = controller
    return controller


def reset_session():
    from logic.global_variables import sess
    for key in sess:
        if key in Sk:
            del sess[key]


def get_email_user_name(email_address: str) -> str:
    return re.match(r'[^@]+', email_address)[0]


def is_valid_email_address(email_address: str) -> bool:
    # From https://stackoverflow.com/a/201378:
    email_regex = r"(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"  # noqa Long line.
    match = re.fullmatch(email_regex, email_address)
    if match is not None:
        from logic.global_variables import cookies
        cookies.set(CookieKeys.LAST_EMAIL_USED, email_address)
        return True
    else:
        return False


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


def dict_of_tables_to_xlsx_bytes(data: dict[str, list[dict[str, Any]]])\
        -> bytes:
    """
    Convert a dict[str, list[dict[str, Any]]] into an Excel file (as bytes).

    Each key in `data` becomes a sheet name, and each list of dicts becomes
    the rows of that sheet (all inner dicts are assumed to share the same keys).
    """
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, rows in data.items():
            df = pd.DataFrame(rows)  # empty list -> empty DataFrame
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    buffer.seek(0)
    return buffer.getvalue()


def database_to_excel_file_bytes() -> bytes:
    data_type = dict[str, list[dict[str, Any]]]
    data: data_type = {
        model.__name__: list(model.select().dicts())
        for model in dahu_2_models
    }
    return dict_of_tables_to_xlsx_bytes(data)


def get_all_email_addresses() -> Iterable[str]:
    try:
        for state in DeteriorationState.select():
            state: DeteriorationState
            yield state.made_by_email
        for modif in FilmModification.select():
            modif: FilmModification
            yield modif.made_by_email
        for film in Film.select():
            film: Film
            yield film.made_by_email
        for target in Target.select():
            target: Target
            yield target.made_by_email
    except:  # TODO
        pass


all_email_addresses = list(set(get_all_email_addresses()))