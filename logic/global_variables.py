import os

import streamlit as st

sess = st.session_state  # Shorthand.

if os.environ['dahu_db_production_mode'] == 'False':
    ON_PRODUCTION = False
elif os.environ['dahu_db_production_mode'] == 'True':
    ON_PRODUCTION = True
else:
    raise ValueError('Invalid value for dahu_db_production_mode. Please add'
                     'environment variable.')