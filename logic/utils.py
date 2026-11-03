"""Small helpers used across the app (strings, emails, URLs, export).

Side effect on import: reads the DB to build `all_email_addresses`.
"""
import io
import os
import re
import secrets
from typing import Any, Iterable
from urllib import parse

import pandas as pd
from peewee import IntegerField

from logic.constants import SessionKeys as Sk, CookieKeys
from logic.lab_modelization.db_models import (dahu_2_models, DeteriorationState,
                                              FilmModification, Film, Target)


def letter_count(text: str) -> int:
    """Counts the ASCII letters (A-Z, any case) in a string.

    Used by `StoichioElement` to check that a parsed composition string
    kept all its element symbols.

    Args:
        text: Any string.

    Returns:
        The number of letters A-Z or a-z.
    """
    upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return len(''.join(i for i in text if i.upper() in upper))


def reset_session():
    """Deletes the app's own entries from `st.session_state`.

    Session state is Streamlit's per-browser-tab dictionary that survives
    reruns. Only the keys listed in `SessionKeys` are removed; others
    (such as the cookie controller) are kept. Called by `init_page` when
    the user arrives from another page.
    """
    from logic.global_variables import sess
    for key in sess:
        if key in Sk:
            del sess[key]


def get_email_user_name(email_address: str) -> str:
    """Returns the part of an email address before the `@`.

    Args:
        email_address: E.g. `'jane.doe@neel.cnrs.fr'`.

    Returns:
        E.g. `'jane.doe'`.
    """
    return re.match(r'[^@]+', email_address)[0]


def is_valid_email_address(email_address: str) -> bool:
    """Checks the syntax of an email address (RFC 5322 regex).

    Called by the email fields' `_validate`. Side effect: when the
    address is valid, saves it in the `LAST_EMAIL_USED` cookie, which
    forms use as their default email.

    Args:
        email_address: The text typed by the user.

    Returns:
        True if the whole string is a valid address.
    """
    # From https://stackoverflow.com/a/201378:
    email_regex = r"(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"  # noqa Long line.
    match = re.fullmatch(email_regex, email_address)
    if match is not None:
        from logic.cookie_init import cookies
        cookies.set(CookieKeys.LAST_EMAIL_USED, email_address)
        return True
    else:
        return False


def get_file_extension(file_name: str):
    """Returns a file name's extension, without the dot.

    Args:
        file_name: E.g. `'map.tar.gz'`.

    Returns:
        E.g. `'gz'`, or `''` if there is no extension.
    """
    return os.path.splitext(file_name)[1].removeprefix('.')


def q_param_str(q_params: dict[str, str|int|IntegerField],
                include_question_mark=False):
    """Builds the query string of a URL, e.g. `lib_id=3&x=a`.

    Query parameters are the `key=value` pairs after the `?` in a URL;
    pages use them to know which object to show. Used to build HTML
    links in `pages/components/general.py`.

    Side effect: converts the values of `q_params` to strings in place.

    Args:
        q_params: Parameter names and values. Can be None or empty.
        include_question_mark: Whether to prefix the result with `?`.

    Returns:
        The URL-encoded query string.
    """
    q_params = q_params or {}
    for k, v in q_params.items():
        # If there are numbers, converts them to strings:
        q_params[k] = str(v)
    string = parse.urlencode(q_params)
    if include_question_mark:
        string = '?' + string
    return string


def to_ascii(str_: str):
    """Replaces non-ASCII characters with XML references (`&#233;`...).

    Used by `switch_page_bttn` to build a widget key from a button label
    that may contain emojis or accents.

    Args:
        str_: Any string.

    Returns:
        An ASCII-only string.
    """
    return str_.encode(  # To bytes.
        'ascii', 'xmlcharrefreplace'
    ).decode('ascii')  # Back to string.


def remove_digits(s: str) -> str:
    """Removes every digit from a string.

    Used to get the element symbols of a composition (`'Fe2O3'` gives
    `'FeO'`).

    Args:
        s: Any string.

    Returns:
        The string without its digits.
    """
    return ''.join([c for c in s if not c.isdigit()])


def rand_str(length=21) -> str:
    """Generates a random string of upper/lowercase letters and digits.

    Uses `secrets`, a cryptographically safe random generator. Used to
    name stored uploaded files.

    Args:
        length: Number of characters.

    Returns:
        The random string.
    """
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def dict_of_tables_to_xlsx_bytes(data: dict[str, list[dict[str, Any]]])\
        -> bytes:
    """
    Convert a dict[str, list[dict[str, Any]]] into an Excel file (as bytes).

    Each key in `data` becomes a sheet name, and each list of dicts becomes
    the rows of that sheet (all inner dicts are assumed to share the same
    keys).

    Args:
        data: Sheet name to list of rows; each row maps column name to
            cell value.

    Returns:
        The content of an .xlsx file.
    """
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, rows in data.items():
            df = pd.DataFrame(rows)  # empty list -> empty DataFrame
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    buffer.seek(0)
    return buffer.getvalue()


def database_to_excel_file_bytes() -> bytes:
    """Exports every table of the DB to an Excel file, one sheet each.

    Used by the download button of the admin page. Values are the raw DB
    values, so physical quantities are in SI base units.

    Returns:
        The content of an .xlsx file.
    """
    data_type = dict[str, list[dict[str, Any]]]
    data: data_type = {
        model.__name__: list(model.select().dicts())
        for model in dahu_2_models
    }
    return dict_of_tables_to_xlsx_bytes(data)


def get_all_email_addresses() -> Iterable[str]:
    """Yields the `made_by_email` of every state, modification, film and
    target in the DB, with duplicates.

    Returns:
        A generator over the addresses.
    """
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


# Choices offered by the email fields of the forms. Computed once, when
# this module is first imported, so addresses added later appear only
# after the app restarts.
all_email_addresses = list(set(get_all_email_addresses()))