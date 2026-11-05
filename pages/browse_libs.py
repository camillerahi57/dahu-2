"""Home page: the table of all libraries, most recently inspected first.

It is the default page (served at the site root). Each row has an
"Inspect" button that opens the library's page. Archived libraries are
hidden unless "Show archived" is checked. When `SHOW_PROBLEM_BANNER` is
True, a banner above the table counts the unread warnings and unsolved
critical errors of the logs.

The experimenter filter in the sidebar is saved in a cookie (a small
piece of text stored by the browser), so it is restored on the next
visit.
"""
import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters

from dahu_2_config import SHOW_PROBLEM_BANNER
from logic.constants import SessionKeys as Sk, IdType, CookieKeys
from logic.lab_modelization.db_models import Library, Film, AppLog
from logic.page_list import pages
from logic.table_columns import LibraryBrowserColumnName as ColName
from logic.utils import get_email_user_name


def body():
    """Draw the page: banner, table, sidebar and filters.

    When an "Inspect" button was clicked, switches to the inspect page
    of that library instead of finishing the drawing.

    Side effects: reads and writes the `CookieKeys.LIB_FILTERS` cookie
    and the `Sk.LIB_FILTERS` session state entry (Streamlit's per-tab
    dictionary that survives reruns).
    """
    # Why these imports are inside the function, unlike in the other
    # browsing pages, is not known (see DOC_NOTES.md).
    from components.browsing import browser_side_bar, INSPECT_BUTTON_KEY, \
        on_inspect_click
    from components.general import init_page, switch_page_bttn, icon
    from logic.global_variables import sess
    from logic.cookie_init import cookies

    init_page(pages.browse_libs, show_home_btn=False)

    st.set_page_config(layout="wide")

    if SHOW_PROBLEM_BANNER:
        problem_banner()

    with st.container(horizontal=True, vertical_alignment='center'):
        switch_page_bttn(pages.new_lib, label="Add a new library",
                         icon_=icon('add_2'))
        show_archived = st.checkbox('Show archived 📦')

    rows = []
    # Ids in the same order as `rows`: the "Inspect" callback finds the
    # library from the index of the clicked row.
    lib_id_list = []
    # Selecting both models with the join loads each film's library in
    # the same SQL query, instead of one extra query per row.
    for film in (Film.select(Film, Library)
                 .join(Library)
                 .order_by(Library.last_inspected_at.desc())):
        library = film.library
        if library.is_archived and not show_archived:
            continue

        lib_name = library.label
        if library.is_archived:
            lib_name += ' · 📦 ARCHIVED'

        rows.append({
            ColName.made_on: film.made_on,
            ColName.lib_name: lib_name,
            ColName.inspect_link: 'Inspect',
            ColName.experimenter: get_email_user_name(film.made_by_email),
            ColName.comment: library.comment,
        })
        lib_id_list.append(library.id)

    column_config = {
        ColName.made_on: st.column_config.DateColumn(help="Date of sputtering.",
                                                     width='small'),
        ColName.lib_name: st.column_config.TextColumn(width='large'),
        ColName.inspect_link: st.column_config.ButtonColumn(
            label='Inspect', width='small', key=INSPECT_BUTTON_KEY,
            on_click=on_inspect_click, args=[lib_id_list]),
        ColName.experimenter: st.column_config.TextColumn(width='small'),
        ColName.comment: st.column_config.TextColumn(width='large'),
    }

    # If we clicked on an inspect button:
    # (`on_inspect_click` set the key before this rerun. `init_page` of
    # the inspect page deletes it, so coming back here does not switch
    # again.)
    if Sk.INSPECT_OBJ_ID in sess:
        lib_id = sess[Sk.INSPECT_OBJ_ID]
        st.switch_page(pages.inspect_lib,
                       query_params={IdType.LIB: str(lib_id)})

    col_order = list(
        column_config)  # Same order as in the column config dictionary.

    df = pd.DataFrame(rows, columns=col_order)

    # `DynamicFilters` keeps the selected filter values in the session
    # state under `filters_name`. Pre-filling that entry from the cookie
    # restores the last filters; the cookie is updated at the end.
    filters_in_cookies = cookies.get(CookieKeys.LIB_FILTERS)
    if filters_in_cookies:
        sess[Sk.LIB_FILTERS] = filters_in_cookies

    possible_filters = [ColName.experimenter]  # TODO ColName.characs
    dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                     filters_name=Sk.LIB_FILTERS)
    browser_side_bar(dynamic_filters, pages.browse_libs)
    dynamic_filters.display_df(hide_index=True, column_config=column_config,
                               height=550)

    cookies.set(CookieKeys.LIB_FILTERS, sess[Sk.LIB_FILTERS])


def problem_banner():
    """Warn about unread warnings and unsolved critical errors.

    Draws nothing when there are none. Otherwise shows the two counts
    (only logs flagged `notify`) and a button to the logs page.
    """
    from components.general import switch_page_bttn

    warning_count = AppLog.unread_warning_notif_count()
    critical_count = AppLog.unsolved_critical_notif_count()
    if warning_count + critical_count == 0:
        return

    msg = "**WARNING**"
    if warning_count > 0:
        msg += f"\n- **{warning_count}** unread warning messages."
    if critical_count > 0:
        msg += f"\n- **{critical_count}** unsolved **critical** errors."
    st.warning(msg)
    switch_page_bttn(pages.view_logs, label='Go to logs', icon_='📃')

    st.divider()


body()
