"""UI helpers shared by every page: page start-up, navigation, links and
date formatting.

A few words used below:

- Query parameter: a `name=value` pair at the end of a page's URL (e.g.
  `?lib_id=3`). Pages use them to know which object to show.
- Session state (`st.session_state`, shortened to `sess`): a dictionary
  that Streamlit keeps for each browser tab. It survives reruns
  (Streamlit re-executes the whole page script after every click).
- Thread: a function running in the background, at the same time as the
  rest of the program, so the page does not wait for it.
"""
from datetime import date as dt_date, datetime
from threading import Thread
from typing import Literal

import keyboard
import streamlit as st
from peewee import DateField, IntegerField
from streamlit.navigation.page import StreamlitPage

from dahu_2_config import DOMAIN, PROBLEM_CHECK_INTERVAL
from logic.constants import (
    SessionKeys as Sk, REDIRECT_PATH, RESOURCE_TYPE, OBJ_ID,
    IdType
)
from logic.db_integrity import get_problems
from logic.global_variables import sess
from logic.lab_modelization.db_models import AppLog
from logic.meta_data_init import app_metadata
from logic.page_list import pages


def init_page(page: StreamlitPage, show_home_btn = True):
    """Run the common start-up steps of a page.

    Every page calls it first. It runs the periodic routines (see
    `run_routines`), draws the Home button, and clears the `SessionKeys`
    entries of the session state when the user arrives from another
    page, so that a form does not show values left by another page.

    Side effects: may start a Restic backup thread and write `AppLog`
    rows (through `run_routines`); writes `Sk.CURRENT_PATH` in the
    session state.

    Args:
        page: The page being drawn (its entry in `logic.page_list.pages`).
        show_home_btn: Whether to draw the Home button. The browsing
            pages pass False: they have the sidebar instead.
    """
    from logic.utils import reset_session

    run_routines()

    if show_home_btn:
        switch_page_bttn(pages.browse_libs, label='Home', icon_='🏠')
    # The session state outlives page changes, so compare with the page
    # seen on the previous run to detect that the user came from
    # elsewhere.
    page_changed = sess.get(Sk.CURRENT_PATH) != page.url_path
    if page_changed:
        reset_session()
        sess[Sk.CURRENT_PATH] = page.url_path


def current_params() -> dict[str, str]:
    """Return the query parameters of the current page's URL.

    Returns:
        Parameter names mapped to their values, as strings.
    """
    return st.query_params.to_dict()


def run_routines():
    """Start a backup and run the problem check when they are due.

    Called by `init_page` on every page load. The due times are in the
    `AppMetadata` singleton (`app_metadata`).

    Side effects:
        - Once `next_backup_at` has passed, starts `Snapshot.backup` in a
          background thread (Restic, `AppMetadata` and `AppLog` writes).
        - Once `next_problem_check_at` has passed, runs `get_problems`
          (which calls Restic), sets the next check time in memory and
          writes one `AppLog` row per problem found.
    """
    from logic.app_restoration import Snapshot

    now = datetime.now()

    if now > app_metadata.next_backup_at:
        # In a thread so the page doesn't wait for Restic. `backup`
        # itself ignores calls made while another backup is running.
        Thread(target=Snapshot.backup).start()

    if now > app_metadata.next_problem_check_at:
        # `get_problems` is a generator: `list` runs all the checks.
        problems = list(get_problems())
        # Read the time again: the checks can take a while.
        now = datetime.now()
        app_metadata.next_problem_check_at = now + PROBLEM_CHECK_INTERVAL
        # TODO save app_metadata.
        for event in problems:
            AppLog.save_new(event)



def colored(text: str, color: str) -> str:
    """Wrap text in Streamlit's Markdown colour syntax.

    Args:
        text: Text to colour.
        color: A colour name Streamlit knows (`'red'`, `'orange'`...).

    Returns:
        `:<color>[<text>]`, to pass to `st.write` or `st.markdown`.
    """
    return f':{color}[{text}]'


def switch_to_submit_successful(
        redirect_to: StreamlitPage|None = None, id_type: IdType|None = None,
        object_id: int|None = None):
    """Go to the "submission successful" page after saving a form.

    The next page and object are passed to that page as query
    parameters (`REDIRECT_PATH`, `RESOURCE_TYPE`, `OBJ_ID`).

    Args:
        redirect_to: Page that the "submission successful" page offers
            to go to next.
        id_type: Kind of the saved object. Only used when `object_id` is
            given.
        object_id: Id of the saved object, to link to its page. An id of
            0 or None adds no link.
    """
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
        q_params: dict[str, str|int|IntegerField]|None = None,
        key: str|None = None,
        type_: Literal["primary", "secondary", "tertiary"] = 'secondary',
        icon_: str|None = None):
    """Draw a button that opens another page.

    Don't use st.switch_page to go from current page P1 to another page P2 if
    P1 has query parameters in its URL. The browser's back button
    will not restore these parameters if the user wants to go back. This will
    break navigation.

    To solve this, use an HTML link instead. This alternative is chosen
    automatically if you use the present function. The link is drawn in
    a bordered box so it looks like a button, but `key` and `type_` are
    then ignored.

    Side effect: converts the values of `q_params` to strings in place.

    Args:
        page: Target page, or its URL path.
        label: Button text. Also used to build the widget key (the name
            Streamlit uses to tell widgets apart) when `key` is None.
        q_params: Query parameters to give to the target page.
        key: Widget key. Needed when two buttons on a page have the same
            label.
        type_: Streamlit button style.
        icon_: Emoji or `icon()` string shown before the label.
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
            st.switch_page(page, query_params=q_params)  # noqa IntegerField is like an int.


def icon(google_material_name: str):
    """Build Streamlit's syntax for a Google Material icon.

    Args:
        google_material_name: Icon name, e.g. `'add_2'` (see
            fonts.google.com/icons).

    Returns:
        `:material/<name>:`, usable in labels and `icon=` arguments.
    """
    return f':material/{google_material_name}:'


def convert_values_to_str(dict_: dict):
    """Convert every value of a dictionary to a string, in place.

    Query parameters must be strings, but callers often pass ids as
    ints or Peewee fields.

    Args:
        dict_: The dictionary to modify.
    """
    for k, v in dict_.items():
        dict_[k] = str(v)


def close_button(label: str = "Close"):
    """Draw a button that presses Ctrl+W to close the browser tab.

    `keyboard` simulates the key press on the computer running the
    Python server, not on the user's computer (see `DOC_NOTES.md`). Not
    called anywhere at the moment.

    Args:
        label: Button text.
    """
    # TODO Not used. Delete?
    if st.button(label):
        keyboard.press_and_release('ctrl+w')


def link_html(label: str, url: str):
    """Build an HTML link that opens in the same browser tab.

    Show it with `st.write(..., unsafe_allow_html=True)`.

    Args:
        label: Link text.
        url: Address to open.

    Returns:
        The `<a>` HTML element, as a string.
    """
    return f"<a href=\"{url}\" target=\"_self\">{label}</a>"


def st_page_link_html(label: str, page: StreamlitPage,
                      q_params: dict[str, str|int|IntegerField]|None = None):
    """Build an HTML link to a page of the app.

    The URL is absolute, built from `DOMAIN`. A link does not break the
    browser's back button, unlike `st.switch_page` (see
    `switch_page_bttn`).

    Side effect: converts the values of `q_params` to strings in place
    (see `logic.utils.q_param_str`).

    Args:
        label: Link text.
        page: Target page.
        q_params: Query parameters to add to the URL.

    Returns:
        The `<a>` HTML element, as a string.
    """
    from logic.utils import q_param_str

    q_param_string = q_param_str(q_params, include_question_mark=True) \
        if q_params else ''
    # The home page is served at the site root, not at its own URL path.
    if page == pages.browse_libs:  # Home page.
        url_path = ''
    else:
        url_path = page.url_path
    url = f'http://{DOMAIN}/{url_path}{q_param_string}'  # noqa No HTTPS.
    return link_html(label, url)


def show_html_link(label: str, page: StreamlitPage, border: bool = False,
                   icon_: str|None = None,
                   q_params: dict[str, str|int|IntegerField]|None = None):
    """Draw a link to a page of the app (see `st_page_link_html`).

    Args:
        label: Link text.
        page: Target page.
        border: Whether to draw a box around the link, so that it looks
            like a button.
        icon_: Emoji or `icon()` string shown before the link.
        q_params: Query parameters to add to the URL. Their values are
            converted to strings in place.
    """
    html = st_page_link_html(label, page, q_params=q_params)
    if icon_:
        html = f'{icon_} {html}'
    if not border:
        st.write(html, unsafe_allow_html=True)
    else:
        with st.container(border=True, width='content'):
            st.write(html, unsafe_allow_html=True)


def email_html(email: str, label: str|None = None):
    """Build an HTML link that opens the user's email program.

    Args:
        email: Email address.
        label: Link text; the address itself if None.

    Returns:
        The `<a href="mailto:...">` HTML element, as a string.
    """
    if label is None:
        label = email
    return f'<a href="mailto:{email}">{label}</a>'


def extensive_date_str(date: DateField):
    """Format a date in words, e.g. `'March 05, 2025'`.

    Args:
        date: A date read from the DB (any object with `year`, `month`
            and `day`).

    Returns:
        The formatted date.
    """
    return dt_date(date.year, date.month, date.day).strftime("%B %d, %Y")


def compact_datetime_str(dt: datetime):
    """Format a date-time for file names, e.g. `'2025-03-05_14-30-00'`.

    Args:
        dt: The date-time.

    Returns:
        The formatted date-time, with no spaces or colons.
    """
    return dt.strftime("%Y-%m-%d_%H-%M-%S")

def datetime_sentence(dt: datetime):
    """Format a date-time in words, e.g.
    `'Wednesday, March 05, 2025 at 14:30:00'`.

    Args:
        dt: The date-time.

    Returns:
        The formatted date-time.
    """
    return dt.strftime("%A, %B %d, %Y at %H:%M:%S")
