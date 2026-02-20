import streamlit as st
import pandas as pd

from entry_point import DahuPages, dahu_host
from tools.constants import lib_id_url_key
from tools.db_schema import Library, CharacMethod, Experimenter
from tools.enums import BrowserColumnName as ColName

st.set_page_config(layout="wide")

if st.button("➕ Add a new library"):
    st.switch_page(DahuPages.add_new)

query = CharacMethod.select(
    CharacMethod.name.alias(ColName.characs),
    Library.made_at.alias(ColName.made_on),
    Library.name.alias(ColName.lib_name),
    Library.id.alias(lib_id_url_key),  # noqa, id is not declared in the project but is in Peewee.
    Experimenter.full_name.alias(ColName.made_by),
    Library.comment.alias(ColName.comment),
).join(Experimenter).switch(CharacMethod).join(Library).dicts()

rows = [row for row in query]
df = pd.DataFrame(rows)

column_config = {
    ColName.made_on: st.column_config.DateColumn(help="Date of sputtering.", width='small'),
    ColName.lib_name: st.column_config.TextColumn(width='large'),
    ColName.inspect_link: st.column_config.LinkColumn(display_text='Inspect', width='small'),
    ColName.characs: st.column_config.ListColumn(width='medium'),
    ColName.made_by: st.column_config.TextColumn(width='small'),
    ColName.comment: st.column_config.TextColumn(width='large'),
}


# noinspection HttpUrlsUsage
inspect_link_df = pd.DataFrame([
    {ColName.inspect_link: f'http://{dahu_host}/{DahuPages.inspect.url_path}'
                           f'?{lib_id_url_key}={row[lib_id_url_key]}'}
    for row in rows
])
df = pd.concat([df, inspect_link_df], axis=1)  # We add it.
col_order = column_config.keys()  # Same order as in the column config dictionary.
df = df[col_order]  # Reorder columns.

st.dataframe(df, hide_index=True, column_config=column_config, height=550)
