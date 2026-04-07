import datetime
from typing import Iterable

import streamlit as st
from pandas import DataFrame

from logic.constants import LIB_ID_URL_KEY
from logic.db_schema import Library, Film, Substrate, FilmLayer
from logic.functions import get_email_user_name
from logic.table_columns import LibInspectColumnName as ColName

lib_id = st.query_params[LIB_ID_URL_KEY]
lib: Library = Library.get_by_id(lib_id)
film: Film = Film.get_by_id(lib.film)
substrate: Substrate = Substrate.get_by_id(film.substrate)
layers: Iterable[FilmLayer] = FilmLayer.select().where(FilmLayer.film == film)
layers = reversed(list(layers))


st.set_page_config(layout="wide", page_title=lib.name)

col1, col2, col3 = st.columns([5, 20, 60])
with col1:
    st.write('**LIBRARY**')
with col2:
    st.subheader(lib.name)
# with col3:
#     delete button


def card(label: str):
    with st.container(border=True, horizontal_alignment='center'):
        st.space()
        st.subheader(label, text_alignment='center')
        st.space()



col1, col2 = st.columns([40, 60])


with col1:
    with st.container(horizontal=True, vertical_alignment='center'):
        card('EDX')
        card('MOKE')
        card('PROFILO')
    with st.container(horizontal=True, vertical_alignment='center'):
        card('X-RAY')
        card('MOKE-2')
        card('EDX-2')

with col2:
    with st.container(border=True):
        email_html = f'<a href="mailto:{lib.film}">{film.made_by_email}</a>'
        date_str = datetime.date(film.made_at.year, film.made_at.month, film.made_at.day).strftime("%B %d, %Y")
        experimenter = get_email_user_name(film.made_by_email)
        st.write(f"Made on **{date_str}** by **{email_html}**.", unsafe_allow_html=True)
        st.write(f"**Label written on sample:** {film.physical_name}")
        st.write(f"**Substrate:** {substrate.name}")
        st.write(f"**Comment:** {lib.comment if lib.comment else '*No comment.*'}")
        st.write(f"**Layers**:")
        table_content = [
            {
                ColName.stoichio: lay.stoichiometry,
                ColName.thickness: lay.thickness,
                ColName.deposit_temp: lay.deposit_temp,
                ColName.deposit_duration: lay.deposit_duration,
                ColName.deposit_power: lay.deposit_power,
            }
            for lay in layers
        ]
        st.dataframe(DataFrame(table_content), hide_index=True, )
