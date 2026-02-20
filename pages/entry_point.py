import streamlit as st
from streamlit.navigation.page import StreamlitPage


dahu_host = 'localhost:8501'

class DahuPages:
    browse = st.Page('browse.py', title='Browse Libraries', icon=":material/edit:")
    add_new = st.Page('add_new.py', title='Add a New Library', icon=":material/edit:")
    inspect = st.Page('inspect.py', title='Inspect a Library', icon=":material/edit:")
    library_added = st.Page('library_added.py', title='New Library Added', icon=":material/edit:")

    @classmethod
    def all_pages(cls):
        return [v for k, v in vars(cls).items() if isinstance(v, StreamlitPage)]

page = st.navigation(DahuPages.all_pages())
page.run()
