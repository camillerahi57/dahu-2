import pandas as pd
from streamlit_dynamic_filters import DynamicFilters
import streamlit as st

from components.browse import on_inspect_click, INSPECT_BUTTON_KEY
from components.streamlit_tools import init_page, switch_button, sess
from logic.page_list import pages
from logic.components import browser_side_bar
from logic.constants import CookieKeys as Ck, IdType, SessionKeys as Sk
from logic.lab_modelization.db_models import Target
from logic.table_columns import TargetBrowserColumnName as ColName
from logic.functions import save_cookies, \
    get_email_user_name

init_page(pages.browse_targets, show_home_btn=False)

st.set_page_config(layout="wide")

switch_button(pages.new_target, label="➕ Add a new target")

query = Target.select(
    Target.made_on.alias(ColName.made_on),
    Target.made_by_email.alias(ColName.made_by),
    Target.label.alias(ColName.label),
    # TargetModel.comment.alias(ColName.comment),
    Target.id.alias(IdType.TARGET),
).dicts()


for row in query:
    row[ColName.made_by] = get_email_user_name(row[ColName.made_by])
    row[ColName.inspect_link] = 'Inspect'

rows = [row for row in query]
target_id_list = [row[IdType.TARGET] for row in query]

column_config = {
    ColName.made_on: st.column_config.DateColumn(width='small'),
    ColName.label: st.column_config.TextColumn(width='large'),
    # ColName.inspect_link: st.column_config.LinkColumn(display_text='Inspect',
    #                                                   width='small'),
    ColName.inspect_link: st.column_config.ButtonColumn(
        label='Inspect', width='small', key=INSPECT_BUTTON_KEY,
        on_click=on_inspect_click, args=[target_id_list]),
    ColName.made_by: st.column_config.TextColumn(width='small'),
    # ColName.comment: st.column_config.TextColumn(width='large'),
}

# If we clicked on an inspect button:
if Sk.INSPECT_OBJ_ID in sess:
    target_id = sess[Sk.INSPECT_OBJ_ID]
    st.switch_page(pages.inspect_target,
                   query_params={IdType.TARGET: str(target_id)})


col_order = list(
    column_config)  # Same order as in the column config dictionary.

df = pd.DataFrame(rows, columns=col_order)

possible_filters = [ColName.made_by]
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Ck.TARGET_FILTERS)
browser_side_bar(dynamic_filters, pages.browse_targets)
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

save_cookies()
