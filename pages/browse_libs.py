import streamlit as st
import pandas as pd
from streamlit_dynamic_filters import DynamicFilters

from logic.components import browser_side_bar
from logic.constants import LIB_ID_URL_KEY, DOMAIN, CookieKeys as Ck
from logic.db_schema import Library, Film
from logic.table_columns import LibraryBrowserColumnName as ColName
from logic.functions import save_session_state, load_session_state, \
    get_email_user_name

sess = load_session_state('browse_libs.py')

st.set_page_config(layout="wide")
if st.button("➕ Add a new library"):
    st.switch_page('new_lib.py')

query = Library.select(
    Library.name.alias(ColName.lib_name),
    Library.id.alias(LIB_ID_URL_KEY),
    # noqa, id is not declared in the project but is in Peewee.
    Library.comment.alias(ColName.comment),
    Film.made_at.alias(ColName.made_on),
    Film.made_by_email.alias(ColName.experimenter)
).join(Film).dicts()

# Python file name (with .py) allows IDE refactorization:
page_name = 'inspect_lib.py'.removesuffix('.py')

for row in query:
    row[ColName.experimenter] = get_email_user_name(row[ColName.experimenter])
    # noinspection HttpUrlsUsage
    row[ColName.inspect_link] = (f"http://{DOMAIN}/{page_name}?"
                                 f"{LIB_ID_URL_KEY}={row[LIB_ID_URL_KEY]}")

rows = [row for row in query]

column_config = {
    ColName.made_on: st.column_config.DateColumn(help="Date of sputtering.",
                                                 width='small'),
    ColName.lib_name: st.column_config.TextColumn(width='large'),
    ColName.inspect_link: st.column_config.LinkColumn(display_text='Inspect',
                                                      width='small'),
    # ColName.characs: st.column_config.ListColumn(width='medium'),
    ColName.experimenter: st.column_config.TextColumn(width='small'),
    ColName.comment: st.column_config.TextColumn(width='large'),
}
col_order = list(
    column_config)  # Same order as in the column config dictionary.

df = pd.DataFrame(rows, columns=col_order)

possible_filters = [ColName.experimenter]  # TODO ColName.characs
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Ck.LIB_FILTERS)
browser_side_bar(dynamic_filters, 'browse_libs.py')
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

save_session_state(sess)
