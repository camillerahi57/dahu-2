"""Page listing all sputtering targets in a table.

Each row has an "Inspect" button that opens the target's page. Archived
targets are hidden unless "Show archived" is checked. The "made by"
filter in the sidebar is saved in a cookie (a small piece of text
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


# `.dicts()` makes the query return one dictionary per row, keyed by the
# aliases, i.e. by the column names of the table shown on the page.
query = Target.select(
    Target.made_on.alias(ColName.made_on),
    Target.made_by_email.alias(ColName.made_by),
    Target.label.alias(ColName.label),
    Target.is_archived.alias(ColName.is_archived),
    Target.id.alias(IdType.TARGET),
).dicts()


# Peewee runs the query once and caches its rows, so iterating `query`
# again below gives these same, modified dictionaries.
for row in query:
    row[ColName.made_by] = get_email_user_name(row[ColName.made_by])
    row[ColName.inspect_link] = 'Inspect'
    if row[ColName.is_archived]:
        row[ColName.label] += ' · 📦 ARCHIVED'

rows = [row for row in query]
if not show_archived:
    rows = [row for row in rows if not row[ColName.is_archived]]

# Built from `rows`, not `query`: the row indexes of the table must match
# the indexes of this list, and `rows` may have dropped archived targets.
target_id_list = [row[IdType.TARGET] for row in rows]

column_config = {
    ColName.made_on: st.column_config.DateColumn(width='small'),
    ColName.label: st.column_config.TextColumn(width='large'),
    ColName.inspect_link: st.column_config.ButtonColumn(
        label='Inspect', width='small', key=INSPECT_BUTTON_KEY,
        on_click=on_inspect_click, args=[target_id_list]),
    ColName.made_by: st.column_config.TextColumn(width='small'),
}

# If we clicked on an inspect button:
# (Set by `on_inspect_click` before this rerun; deleted by `init_page`
# of the inspect page.)
if Sk.INSPECT_OBJ_ID in sess:
    target_id = sess[Sk.INSPECT_OBJ_ID]
    st.switch_page(pages.inspect_target,
                   query_params={IdType.TARGET: str(target_id)})


col_order = list(
    column_config)  # Same order as in the column config dictionary.

df = pd.DataFrame(rows, columns=col_order)

# Restore the last filters from the cookie into the session state entry
# that `DynamicFilters` reads; the cookie is updated at the end.
filters_in_cookies = new_controller().get(CookieKeys.TARGET_FILTERS)
if filters_in_cookies:
    sess[Sk.TARGET_FILTERS] = filters_in_cookies

possible_filters = [ColName.made_by]
dynamic_filters = DynamicFilters(df, filters=possible_filters,
                                 filters_name=Sk.TARGET_FILTERS)

browser_side_bar(dynamic_filters, pages.browse_targets)
# `on_inspect_click` receives this same list object: refill it in place
# with the displayed rows only (the clicked row is a position in the
# filtered table).
target_id_list[:] = filtered_ids(dynamic_filters, target_id_list)
dynamic_filters.display_df(hide_index=True, column_config=column_config,
                           height=550)

new_controller().set(CookieKeys.TARGET_FILTERS, sess[Sk.TARGET_FILTERS])
