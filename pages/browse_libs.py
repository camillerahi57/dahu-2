import streamlit as st
import pandas as pd
from streamlit_dynamic_filters import DynamicFilters

from logic.components import browser_side_bar
from logic.constants import LIB_ID_URL_KEY, DOMAIN, StorageKeys as Sk
from logic.db_schema import Library, CharacMethod, Experimenter
from logic.enums import LibraryBrowserColumnName as ColName
from logic.functions import session_to_cookies, load_session_state


sess = load_session_state()

st.set_page_config(layout="wide")
if st.button("➕ Add a new library"):
    st.switch_page('new_lib.py')

query = CharacMethod.select(
    CharacMethod.name.alias(ColName.characs),
    Library.made_at.alias(ColName.made_on),
    Library.name.alias(ColName.lib_name),
    Library.id.alias(LIB_ID_URL_KEY),  # noqa, id is not declared in the project but is in Peewee.
    Experimenter.full_name.alias(ColName.experimenter),
    Library.comment.alias(ColName.comment),
).join(Experimenter).switch(CharacMethod).join(Library).dicts()

rows = [row for row in query]
df = pd.DataFrame(rows)

column_config = {
    ColName.made_on: st.column_config.DateColumn(help="Date of sputtering.", width='small'),
    ColName.lib_name: st.column_config.TextColumn(width='large'),
    ColName.inspect_link: st.column_config.LinkColumn(display_text='Inspect', width='small'),
    ColName.characs: st.column_config.ListColumn(width='medium'),
    ColName.experimenter: st.column_config.TextColumn(width='small'),
    ColName.comment: st.column_config.TextColumn(width='large'),
}


inspect_path = 'inspect_lib.py'.removesuffix('.py')  # Weird but helps IDE refactorization.
# noinspection HttpUrlsUsage
inspect_link_df = pd.DataFrame([
    {ColName.inspect_link: f"http://{DOMAIN}/{inspect_path}"  # TODO Add HTTPS.
                           f'?{LIB_ID_URL_KEY}={row[LIB_ID_URL_KEY]}'}
    for row in rows
])
df = pd.concat([df, inspect_link_df], axis=1)  # We add it.
col_order = column_config.keys()  # Same order as in the column config dictionary.
df = df[col_order]  # Reorder columns.

possible_filters = [ColName.experimenter, ColName.characs]
dynamic_filters = DynamicFilters(df, filters=possible_filters, filters_name=Sk.LIB_FILTERS)
browser_side_bar(dynamic_filters, 'browse_libs.py')
dynamic_filters.display_df(hide_index=True, column_config=column_config, height=550)


session_to_cookies(sess)