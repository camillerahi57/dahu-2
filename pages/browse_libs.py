import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters

from components.browsing import browser_side_bar, INSPECT_BUTTON_KEY, \
    on_inspect_click
from components.general import init_page, sess, switch_page_bttn, cookies
from dahu_2_config import SHOW_PROBLEM_BANNER
from logic.constants import SessionKeys as Sk, IdType, CookieKeys
from logic.lab_modelization.db_models import Library, Film, AppLog
from logic.page_list import pages
from logic.table_columns import LibraryBrowserColumnName as ColName
from logic.utils import get_email_user_name

init_page(pages.browse_libs, show_home_btn=False)

st.set_page_config(layout="wide")

def body():
    if SHOW_PROBLEM_BANNER:
        problem_banner()

    with st.container(horizontal=True, vertical_alignment='center'):
        switch_page_bttn(pages.new_lib, label="Add a new library", icon_='➕')
        show_archived = st.checkbox('Show archived 📦')

    query = Library.select(
        Library.label.alias(ColName.lib_name),
        Library.id.alias(IdType.LIB),
        Library.comment.alias(ColName.comment),
        Film.made_on.alias(ColName.made_on),
        Film.made_by_email.alias(ColName.experimenter),
        Library.is_archived.alias(ColName.is_archived),
    ).join(Film).dicts()


    for row in query:
        experimenter = row[ColName.experimenter]
        row[ColName.experimenter] = get_email_user_name(experimenter)
        row[ColName.inspect_link] = 'Inspect'
        if row[ColName.is_archived]:
            row[ColName.lib_name] += ' · 📦 ARCHIVED'

    rows = [row for row in query]
    if not show_archived:
        rows = [row for row in rows if not row[ColName.is_archived]]

    lib_id_list = [row[IdType.LIB] for row in query]

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
    if Sk.INSPECT_OBJ_ID in sess:
        lib_id = sess[Sk.INSPECT_OBJ_ID]
        st.switch_page(pages.inspect_lib,
                       query_params={IdType.LIB: str(lib_id)})

    col_order = list(
        column_config)  # Same order as in the column config dictionary.

    df = pd.DataFrame(rows, columns=col_order)

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