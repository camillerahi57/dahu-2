import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters

from logic.components import browser_side_bar
from logic.constants import CookieKeys as Ck
from logic.db_schema import Substrate
from logic.table_columns import SubstrateBrowserColumnName as ColName
from logic.functions import load_session_state, save_session_state

sess = load_session_state('browse_substrates.py')

st.set_page_config(layout="wide")

if st.button("➕ Add a new substrate"):
    st.switch_page('new_substrate.py')

query = Substrate.select(
    Substrate.name.alias(ColName.name),
    Substrate.comment.alias(ColName.comment),
    Substrate.id,
).dicts()

page_name = 'inspect_target.py'.removesuffix('.py')  # Using the file name
# allows refactorization.

rows = [row for row in query]

column_config = {
    ColName.name: st.column_config.TextColumn(width='small'),
    ColName.comment: st.column_config.TextColumn(width='large'),
}

col_order = column_config.keys()  # Same order as in the column config
# dictionary.

df = pd.DataFrame(rows, columns=list(col_order))

possible_filters = [ColName.name]
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Ck.SUBSTRATE_FILTERS)
browser_side_bar(dynamic_filters, 'browse_substrates.py')
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

save_session_state(sess)
