from datetime import date as dt_date, datetime
from random import random
from threading import Thread
from typing import Literal

import keyboard
import streamlit as st
from peewee import DateField
from streamlit.navigation.page import StreamlitPage

from dahu_2_config import DOMAIN
from logic.constants import (
    SessionKeys as Sk, REDIRECT_PATH, RESOURCE_TYPE, OBJ_ID,
    IdType
)
from logic.db_integrity import get_problems
from logic.lab_modelization.base_classes import Event
from logic.lab_modelization.db_enums import EventType, LogSeverity
from logic.lab_modelization.db_models import AppMetadata, AppLog
from logic.page_list import pages
from logic.utils import new_controller

sess = st.session_state  # Shorthand.
cookies = new_controller()
app_metadata = AppMetadata.get_or_new()


def init_page(page: StreamlitPage, show_home_btn = True):
    from logic.utils import reset_session

    run_routines()

    if show_home_btn:
        switch_page_bttn(pages.browse_libs, label='Home', icon_='🏠')
    page_changed = sess.get(Sk.CURRENT_PATH) != page.url_path
    if page_changed:
        reset_session()
        sess[Sk.CURRENT_PATH] = page.url_path


def current_params() -> dict[str, str]:
    return st.query_params.to_dict()


def run_routines():
    now = datetime.now()

    if now > app_metadata.next_backup_at:
        from logic.app_restoration import Snapshot
        Thread(target=Snapshot.backup).start()

    if now > app_metadata.next_problem_check_at:
        for event in get_problems():
            AppLog.save_new(event)

        # For testing:

        # if random() > .5:
        #     event = Event(EventType.UNKNOWN_ENUM, True, LogSeverity.CRITICAL,
        #                   f'BE CAREFUL {random()}')
        #     AppLog.save_new(event)
        #
        # if random() > .5:
        #     event = Event(EventType.NO_RECENT_BACKUP, True,
        #                   LogSeverity.WARNING,
        #                   f'WOW CALM DOWN')
        #     AppLog.save_new(event)


def colored(text: str, color: str) -> str:
    return f':{color}[{text}]'


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
        icon_: str = None):
    """
    Don't use st.switch_page to go from current page P1 to another page P2 if
    P1 has query parameters in its URL. The browser's back button
    will not restore these parameters if the user wants to go back. This will
    break navigation.

    To solve his, use an HTML link instead. This alternative is chosen
    automatically if you use the present function.
    """
    from logic.utils import to_ascii

    if isinstance(page, str):
        page = pages.from_url_path(page)

    q_params = q_params or {}
    convert_values_to_str(q_params)

    if not key:
        key = to_ascii(label)  # Create a key from label.

    # If there currently are q_parameters:
    if len(current_params()) > 0:
        show_html_link(label, page, border=True, icon_=icon_, q_params=q_params)
    else:
        bttn_label = f'{icon_} {label}' if icon_ else label
        if st.button(bttn_label, key=key, type=type_):
            st.switch_page(page, query_params=q_params)


def icon(google_material_name: str):
    return f':material/{google_material_name}:'


def convert_values_to_str(dict_: dict):
    for k, v in dict_.items():
        dict_[k] = str(v)


def close_button(label: str = "Close"):
    if st.button(label):
        keyboard.press_and_release('ctrl+w')


def link_html(label: str, url: str):
    return f"<a href=\"{url}\" target=\"_self\">{label}</a>"


def st_page_link_html(label: str, page: StreamlitPage,
                      q_params: dict[str, str|int] = None):
    from logic.utils import q_param_str

    q_param_string = q_param_str(q_params, include_question_mark=True) \
        if q_params else ''
    if page == pages.browse_libs:  # Home page.
        url_path = ''
    else:
        url_path = page.url_path
    url = f'http://{DOMAIN}/{url_path}{q_param_string}'  # noqa
    # TODO HTTPS?
    return link_html(label, url)


def show_html_link(label: str, page: StreamlitPage, border: bool = False,
                   icon_: str = None, q_params: dict[str, str | int] = None):
    html = st_page_link_html(label, page, q_params=q_params)
    if icon_:
        html = f'{icon_} {html}'
    if not border:
        st.write(html, unsafe_allow_html=True)
    else:
        with st.container(border=True, width='content'):
            st.write(html, unsafe_allow_html=True)


def email_html(email: str, label: str=None):
    if label is None:
        label = email
    return f'<a href="mailto:{email}">{label}</a>'


def extensive_date_str(date: DateField):
    return dt_date(date.year, date.month, date.day).strftime("%B %d, %Y")


def compact_datetime_str(dt: datetime):
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

def datetime_sentence(dt: datetime):
    return dt.strftime("%A, %B %d, %Y at %H:%M:%S")