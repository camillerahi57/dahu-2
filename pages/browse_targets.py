import pandas as pd
from streamlit_dynamic_filters import DynamicFilters
import streamlit as st

from logic.components import browser_side_bar
from logic.constants import StorageKeys as Sk
from logic.enums import TargetBrowserColumnName as ColName
from logic.functions import load_session_state, session_to_cookies

sess = load_session_state()

st.set_page_config(layout="wide")

if st.button("➕ Add a new target"):
    st.switch_page('new_target.py')

rows = [
    {
        ColName.made_on: 123456789,
        ColName.target_name: 'TargetBlahBlah',
        ColName.made_by: 'Pierre',
        ColName.comment: 'What a great target',
    }
]

df = pd.DataFrame(rows)

column_config = {
    ColName.made_on: st.column_config.DateColumn(help="Date of sputtering.", width='small'),
    ColName.target_name: st.column_config.TextColumn(width='large'),
    ColName.made_by: st.column_config.TextColumn(width='small'),
    ColName.comment: st.column_config.TextColumn(width='large'),
}

possible_filters = [ColName.made_by]
dynamic_filters = DynamicFilters(df, filters=possible_filters, filters_name=Sk.TARGET_FILTERS)
browser_side_bar(dynamic_filters, 'browse_targets.py')
dynamic_filters.display_df(hide_index=True, column_config=column_config, height=550)

session_to_cookies(sess)