import streamlit as st


st.title('New state added ✔')
if st.button('Go to targets'):
    st.switch_page('browse_targets.py')