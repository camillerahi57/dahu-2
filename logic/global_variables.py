import streamlit as st

from logic.lab_modelization.db_models import AppMetadata
from logic.utils import new_controller

sess = st.session_state  # Shorthand.
cookies = new_controller()
app_metadata = AppMetadata.get_or_new()
