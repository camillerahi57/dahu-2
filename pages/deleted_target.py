import streamlit as st


st.title('Target successfully deleted.')
if st.button('Go to targets'):
    st.switch_page('browse_targets.py')