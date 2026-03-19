import pandas as pd
from streamlit_dynamic_filters import DynamicFilters
import streamlit as st

from logic.components import browser_side_bar
from logic.constants import StorageKeys as Sk
from logic.db_schema import Target
from logic.enums import TargetBrowserColumnName as ColName
from logic.functions import load_session_state, save_session_state, email_user_name

sess = load_session_state('browse_targets.py')

st.set_page_config(layout="wide")

if st.button("➕ Add a new target"):
    st.switch_page('new_target.py')

query = Target.select(
    Target.made_at.alias(ColName.made_on),
    Target.made_by_email.alias(ColName.made_by),
    Target.target_name.alias(ColName.target_name),
    Target.comment.alias(ColName.comment),
).dicts()

for row in query:
    row[ColName.made_by] = email_user_name(row[ColName.made_by])

rows = [row for row in query]

column_config = {
    ColName.made_on: st.column_config.DateColumn(width='small'),
    ColName.target_name: st.column_config.TextColumn(width='large'),
    ColName.made_by: st.column_config.TextColumn(width='small'),
    ColName.comment: st.column_config.TextColumn(width='large'),
}

if len(rows) > 0:
    df = pd.DataFrame(rows)
else:
    df = pd.DataFrame(columns=list(column_config))

possible_filters = [ColName.made_by]
dynamic_filters = DynamicFilters(df, filters=possible_filters, filters_name=Sk.TARGET_FILTERS)
browser_side_bar(dynamic_filters, 'browse_targets.py')
dynamic_filters.display_df(hide_index=True, column_config=column_config, height=550)

save_session_state(sess)