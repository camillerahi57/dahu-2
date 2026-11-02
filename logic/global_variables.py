"""Variables that many modules need: the Streamlit session state and the
production/development switch.

Importing this module reads the Windows environment variable
`dahu_db_production_mode` and imports Streamlit.
"""

import os

import streamlit as st

# Shorthand for `st.session_state`, a dictionary that Streamlit keeps for
# each browser tab. It survives reruns (Streamlit re-executes the page
# script after each click).
sess = st.session_state  # Shorthand.

# True when the app runs on the production PC, False in development.
# It selects the settings block in `dahu_2_config.py`. Any other value of
# the environment variable raises an error at import (a missing variable
# raises a `KeyError`), so no settings block is chosen by default.
if os.environ['dahu_db_production_mode'] == 'False':
    ON_PRODUCTION = False
elif os.environ['dahu_db_production_mode'] == 'True':
    ON_PRODUCTION = True
else:
    raise ValueError('Invalid value for dahu_db_production_mode. Please add'
                     'environment variable.')
