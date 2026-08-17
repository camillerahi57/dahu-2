import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters

from components.browse import on_inspect_click, INSPECT_BUTTON_KEY
from components.streamlit_tools import init_page, sess, switch_page_bttn
from logic.components import browser_side_bar
from logic.constants import CookieKeys as Ck, \
    SessionKeys as Sk, IdType
from logic.functions import save_cookies, \
    get_email_user_name
from logic.lab_modelization.db_models import Library, Film
from logic.page_list import pages
from logic.table_columns import LibraryBrowserColumnName as ColName

init_page(pages.browse_libs, show_home_btn=False)

st.set_page_config(layout="wide")

with st.container(horizontal=True, vertical_alignment='center'):
    switch_page_bttn(pages.new_lib, label="Add a new library", icon='➕')
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
    st.switch_page(pages.inspect_lib, query_params={IdType.LIB: str(lib_id)})
    
col_order = list(
    column_config)  # Same order as in the column config dictionary.

df = pd.DataFrame(rows, columns=col_order)

possible_filters = [ColName.experimenter]  # TODO ColName.characs
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Ck.LIB_FILTERS)
browser_side_bar(dynamic_filters, pages.browse_libs)
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

save_cookies()
