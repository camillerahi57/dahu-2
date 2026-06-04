import streamlit as st

from logic.constants import REDIRECT_PATH_URL_KEY, ID_KEY_URL_KEY, \
    ID_VALUE_URL_KEY
from logic.page_list import pages

redirect_path = st.query_params[REDIRECT_PATH_URL_KEY]
redirect_id_key = st.query_params[ID_KEY_URL_KEY]
redirect_id_value = st.query_params[ID_VALUE_URL_KEY]

redirect_query_params = {
    redirect_id_key: redirect_id_value,
}

st.title('Submission Successful ✔')
if st.button('Continue'):
    redirect_page = pages.from_url_path(redirect_path)
    st.switch_page(redirect_page, query_params=redirect_query_params)