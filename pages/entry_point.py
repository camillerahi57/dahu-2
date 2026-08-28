import streamlit as st

from logic.page_list import pages

# Don't import anything from this file, as it will run it again and re-run
# the current page.

page = st.navigation(list(pages))

page.run()