import streamlit as st


st.title('New Substrate Added ✔')
if st.button('Browse substrates'):
    st.switch_page('browse_substrates.py')