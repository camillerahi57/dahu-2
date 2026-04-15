import streamlit as st


st.title('Substrate successfully deleted.')
if st.button('Go to substrates'):
    st.switch_page('browse_substrates.py')