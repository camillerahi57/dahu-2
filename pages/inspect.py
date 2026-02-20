import streamlit as st

from tools.constants import lib_id_url_key
from tools.db_schema import Library


lib_id = int(st.query_params[lib_id_url_key])
lib: Library = Library.get_by_id(lib_id)
st.title(f"Library “{lib.name}”")