import streamlit as st

from entry_point import DahuPages


st.title('New library Added ✔')
if st.button('Go to home page'):
    st.switch_page(DahuPages.browse)