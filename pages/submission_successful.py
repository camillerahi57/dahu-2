import streamlit as st

from components.general import init_page, current_params, switch_page_bttn
from logic.constants import REDIRECT_PATH, RESOURCE_TYPE, OBJ_ID
from logic.page_list import pages

init_page(pages.submission_successful)


if REDIRECT_PATH in current_params():
    redirect_path = current_params()[REDIRECT_PATH]
else:
    redirect_path = None

if OBJ_ID in current_params():
    obj_type = current_params()[RESOURCE_TYPE]
    obj_id = current_params()[OBJ_ID]
    redirect_q_params = {obj_type: obj_id}
else:
    redirect_q_params = None


st.title('Submission Successful ✔')

if redirect_path:
    switch_page_bttn(
        redirect_path, label='Continue', q_params=redirect_q_params
    )
else:
    switch_page_bttn(pages.browse_libs, label='Home', icon_='🏠', key='home2')