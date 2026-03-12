import streamlit as st

from logic.constants import LIB_ID_URL_KEY
from logic.db_schema import Library


lib_id = int(st.query_params[LIB_ID_URL_KEY])
lib: Library = Library.get_by_id(lib_id)
st.title(f"Library “{lib.name}”")