import streamlit as st

from pages import PageEnum

# Don't import anything from this file, as it will run it again and re-run
# the current page.


page = st.navigation([enum.value for enum in PageEnum])

page.run()