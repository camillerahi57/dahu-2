"""Page listing all substrates in a table.

Each row has an "Inspect" button that opens the substrate's page. The
label filter in the sidebar is saved in a cookie (a small piece of text
stored by the browser), so it is restored on the next visit. See
`browse_libs.py` for the same mechanisms, explained.
"""
import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters

from components.browsing import browser_side_bar, INSPECT_BUTTON_KEY, \
    on_inspect_click, filtered_ids
from components.general import init_page, switch_page_bttn, icon
from logic.constants import CookieKeys, IdType, SessionKeys as Sk
from logic.cookie_init import new_controller
from logic.global_variables import sess
from logic.lab_modelization.db_models import Substrate
from logic.page_list import pages
from logic.table_columns import SubstrateBrowserColumnName as ColName

init_page(pages.browse_substrates, show_home_btn=False)

st.set_page_config(layout="wide")

switch_page_bttn(pages.new_substrate, label="Add a new substrate",
                 icon_=icon('add_2'))

# One dictionary per row, keyed by the column names of the table shown.
query = Substrate.select(
    Substrate.label.alias(ColName.label),
    Substrate.comment.alias(ColName.comment),
    Substrate.id.alias(IdType.SUB),
).dicts()

rows = list(query)
# Iterating `query` again reuses Peewee's cached rows (no second SQL
# query). Ids are in the same order as `rows`, for `on_inspect_click`.
sub_id_list = [row[IdType.SUB] for row in query]

for row in rows:
    row[ColName.inspect_link] = 'Inspect'

column_config = {
    ColName.label: st.column_config.TextColumn(width='small'),
    ColName.inspect_link: st.column_config.ButtonColumn(
        label='Inspect', width='small', key=INSPECT_BUTTON_KEY,
        on_click=on_inspect_click, args=[sub_id_list]),
    ColName.comment: st.column_config.TextColumn(width='large'),
}

# If we clicked on an inspect button:
# (Set by `on_inspect_click` before this rerun; deleted by `init_page`
# of the inspect page.)
if Sk.INSPECT_OBJ_ID in sess:
    sub_id = sess[Sk.INSPECT_OBJ_ID]
    st.switch_page(pages.inspect_substrate,
                   query_params={IdType.SUB: str(sub_id)})

col_order = column_config.keys()  # Same order as in the column config
# dictionary.

df = pd.DataFrame(rows, columns=list(col_order))

# Restore the last filters from the cookie into the session state entry
# that `DynamicFilters` reads; the cookie is updated at the end.
filters_in_cookies = new_controller().get(CookieKeys.SUBSTRATE_FILTERS)
if filters_in_cookies:
    sess[Sk.SUBSTRATE_FILTERS] = filters_in_cookies

possible_filters = [ColName.label]
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Sk.SUBSTRATE_FILTERS)
browser_side_bar(dynamic_filters, pages.browse_substrates)
# `on_inspect_click` receives this same list object: refill it in place
# with the displayed rows only (the clicked row is a position in the
# filtered table).
sub_id_list[:] = filtered_ids(dynamic_filters, sub_id_list)
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

new_controller().set(CookieKeys.SUBSTRATE_FILTERS, sess[Sk.SUBSTRATE_FILTERS])
