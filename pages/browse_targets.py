import pandas as pd
import streamlit as st
from streamlit_dynamic_filters import DynamicFilters

from components.browsing import browser_side_bar, INSPECT_BUTTON_KEY, \
    on_inspect_click
from components.general import init_page, switch_page_bttn, icon
from logic.global_variables import sess, cookies
from logic.constants import CookieKeys, IdType, SessionKeys as Sk
from logic.lab_modelization.db_models import Target
from logic.page_list import pages
from logic.table_columns import TargetBrowserColumnName as ColName
from logic.utils import get_email_user_name

init_page(pages.browse_targets, show_home_btn=False)

st.set_page_config(layout="wide")

with st.container(horizontal=True, vertical_alignment='center'):
    switch_page_bttn(pages.new_target, label="Add a new target",
                     icon_=icon('add_2'))
    show_archived = st.checkbox('Show archived 📦')


query = Target.select(
    Target.made_on.alias(ColName.made_on),
    Target.made_by_email.alias(ColName.made_by),
    Target.label.alias(ColName.label),
    Target.is_archived.alias(ColName.is_archived),
    Target.id.alias(IdType.TARGET),
).dicts()


for row in query:
    row[ColName.made_by] = get_email_user_name(row[ColName.made_by])
    row[ColName.inspect_link] = 'Inspect'
    if row[ColName.is_archived]:
        row[ColName.label] += ' · 📦 ARCHIVED'

rows = [row for row in query]
if not show_archived:
    rows = [row for row in rows if not row[ColName.is_archived]]

target_id_list = [row[IdType.TARGET] for row in query]

column_config = {
    ColName.made_on: st.column_config.DateColumn(width='small'),
    ColName.label: st.column_config.TextColumn(width='large'),
    ColName.inspect_link: st.column_config.ButtonColumn(
        label='Inspect', width='small', key=INSPECT_BUTTON_KEY,
        on_click=on_inspect_click, args=[target_id_list]),
    ColName.made_by: st.column_config.TextColumn(width='small'),
}

# If we clicked on an inspect button:
if Sk.INSPECT_OBJ_ID in sess:
    target_id = sess[Sk.INSPECT_OBJ_ID]
    st.switch_page(pages.inspect_target,
                   query_params={IdType.TARGET: str(target_id)})


col_order = list(
    column_config)  # Same order as in the column config dictionary.

df = pd.DataFrame(rows, columns=col_order)

filters_in_cookies = cookies.get(CookieKeys.TARGET_FILTERS)
if filters_in_cookies:
    sess[Sk.TARGET_FILTERS] = filters_in_cookies

possible_filters = [ColName.made_by]
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Sk.TARGET_FILTERS)

browser_side_bar(dynamic_filters, pages.browse_targets)
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

cookies.set(CookieKeys.TARGET_FILTERS, sess[Sk.TARGET_FILTERS])
