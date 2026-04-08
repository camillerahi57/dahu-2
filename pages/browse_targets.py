import pandas as pd
from streamlit_dynamic_filters import DynamicFilters
import streamlit as st

from logic.components import browser_side_bar
from logic.constants import CookieKeys as Ck, DOMAIN, TARGET_ID_URL_KEY
from logic.db_schema import Target
from logic.table_columns import TargetBrowserColumnName as ColName
from logic.functions import load_session_state, save_session_state, \
    get_email_user_name

sess = load_session_state('browse_targets.py')

st.set_page_config(layout="wide")

if st.button("➕ Add a new target"):
    st.switch_page('new_target.py')

query = Target.select(
    Target.made_at.alias(ColName.made_on),
    Target.made_by_email.alias(ColName.made_by),
    Target.physical_name.alias(ColName.physical_name),
    Target.comment.alias(ColName.comment),
    Target.id,
).dicts()

page_name = 'inspect_target.py'.removesuffix(
    '.py')  # Using the file name allows refactorization.

for row in query:
    row[ColName.made_by] = get_email_user_name(row[ColName.made_by])
    # noinspection HttpUrlsUsage
    row[ColName.inspect_link] = (f"http://{DOMAIN}/{page_name}?"
                                 f"{TARGET_ID_URL_KEY}={row['id']}")  # noqa

rows = [row for row in query]

column_config = {
    ColName.made_on: st.column_config.DateColumn(width='small'),
    ColName.physical_name: st.column_config.TextColumn(width='large'),
    ColName.inspect_link: st.column_config.LinkColumn(display_text='Inspect',
                                                      width='small'),
    ColName.made_by: st.column_config.TextColumn(width='small'),
    ColName.comment: st.column_config.TextColumn(width='large'),
}
col_order = list(
    column_config)  # Same order as in the column config dictionary.

df = pd.DataFrame(rows, columns=col_order)

possible_filters = [ColName.made_by]
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Ck.TARGET_FILTERS)
browser_side_bar(dynamic_filters, 'browse_targets.py')
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

save_session_state(sess)
