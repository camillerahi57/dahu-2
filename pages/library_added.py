import streamlit as st


st.title('New library Added ✔')
if st.button('Go to home page'):
    st.switch_page('browse_libs.py')