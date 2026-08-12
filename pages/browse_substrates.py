import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters

from components.browse import INSPECT_BUTTON_KEY, on_inspect_click
from components.streamlit_tools import init_page, switch_page_bttn, sess
from logic.components import browser_side_bar
from logic.constants import CookieKeys as Ck, IdType, SessionKeys as Sk
from logic.functions import save_cookies
from logic.lab_modelization.db_models import Substrate
from logic.page_list import pages
from logic.table_columns import SubstrateBrowserColumnName as ColName

init_page(pages.browse_substrates, show_home_btn=False)

st.set_page_config(layout="wide")

switch_page_bttn(pages.new_substrate, label="➕ Add a new substrate")

query = Substrate.select(
    Substrate.label.alias(ColName.label),
    Substrate.comment.alias(ColName.comment),
    Substrate.id.alias(IdType.SUB),
).dicts()

rows = list(query)
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
if Sk.INSPECT_OBJ_ID in sess:
    sub_id = sess[Sk.INSPECT_OBJ_ID]
    st.switch_page(pages.inspect_substrate,
                   query_params={IdType.SUB: str(sub_id)})

col_order = column_config.keys()  # Same order as in the column config
# dictionary.

df = pd.DataFrame(rows, columns=list(col_order))

possible_filters = [ColName.label]
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Ck.SUBSTRATE_FILTERS)
browser_side_bar(dynamic_filters, pages.browse_substrates)
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

save_cookies()
