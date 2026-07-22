import streamlit as st
import pandas as pd
from streamlit_dynamic_filters import DynamicFilters

from components.browse_libs import on_inspect_click, INSPECT_BUTTON_KEY
from logic.page_list import pages
from logic.components import browser_side_bar
from logic.constants import LIB_ID_URL_KEY, DOMAIN, CookieKeys as Ck, \
    SessionKeys as Sk
from logic.lab_modelization.db_models import Library, Film
from logic.table_columns import LibraryBrowserColumnName as ColName
from logic.functions import save_cookies, new_session_state, \
    get_email_user_name

sess = new_session_state(pages.browse_libs)

st.set_page_config(layout="wide")
if st.button("➕ Add a new library"):
    st.switch_page('new_lib.py')

query = Library.select(
    Library.label.alias(ColName.lib_name),
    Library.id.alias(LIB_ID_URL_KEY),
    Library.comment.alias(ColName.comment),
    Film.made_on.alias(ColName.made_on),
    Film.made_by_email.alias(ColName.experimenter)
).join(Film).dicts()

# Python file name (with .py) allows IDE refactorization:
page_name = pages.inspect_lib.url_path

for row in query:
    row[ColName.experimenter] = get_email_user_name(row[ColName.experimenter])
    # noinspection HttpUrlsUsage
    # row[ColName.inspect_link] = (f"http://{DOMAIN}/{page_name}?"
    #                              f"{LIB_ID_URL_KEY}={row[LIB_ID_URL_KEY]}")
    row[ColName.inspect_link] = 'Inspect'

rows = [row for row in query]
lib_idx_list = [row[LIB_ID_URL_KEY] for row in query]

column_config = {
    ColName.made_on: st.column_config.DateColumn(help="Date of sputtering.",
                                                 width='small'),
    ColName.lib_name: st.column_config.TextColumn(width='large'),
    ColName.inspect_link: st.column_config.ButtonColumn(
        label='Inspect', width='small', key=INSPECT_BUTTON_KEY,
        on_click=on_inspect_click, args=[lib_idx_list]),
    # ColName.inspect_link: st.column_config.LinkColumn(display_text='Inspect',
    #                                                   width='small'),
    # ColName.characs: st.column_config.ListColumn(width='medium'),
    ColName.experimenter: st.column_config.TextColumn(width='small'),
    ColName.comment: st.column_config.TextColumn(width='large'),
}

# If we clicked on an inspect lib button:
if Sk.SWITCH_PAGE_REQUEST_LIB_ID in sess:
    lib_id = sess[Sk.SWITCH_PAGE_REQUEST_LIB_ID]
    st.switch_page(pages.inspect_lib,
                   query_params={LIB_ID_URL_KEY: str(lib_id)})
    
col_order = list(
    column_config)  # Same order as in the column config dictionary.

df = pd.DataFrame(rows, columns=col_order)

possible_filters = [ColName.experimenter]  # TODO ColName.characs
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Ck.LIB_FILTERS)
browser_side_bar(dynamic_filters, 'browse_libs.py')
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

save_cookies(sess)
