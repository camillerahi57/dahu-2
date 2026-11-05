"""Confirmation page shown after a form was saved.

Pages reach it through `switch_to_submit_successful`, which passes in
the URL's query parameters (the `name=value` pairs after `?`):

- `REDIRECT_PATH`: URL path of the page to go to next;
- `RESOURCE_TYPE` and `OBJ_ID`: the `IdType` name and the id of the
  saved object, given to that next page as its own query parameter
  (e.g. `?lib_id=3`).

The page shows a "Continue" button to that next page, or a "Home"
button when no next page was given.
"""
import streamlit as st

from components.general import init_page, current_params, switch_page_bttn
from logic.constants import REDIRECT_PATH, RESOURCE_TYPE, OBJ_ID
from logic.page_list import pages

init_page(pages.submission_successful)


if REDIRECT_PATH in current_params():
    redirect_path = current_params()[REDIRECT_PATH]
else:
    redirect_path = None

# `switch_to_submit_successful` always sets `RESOURCE_TYPE` together with
# `OBJ_ID`.
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
    # `init_page` already drew a Home button whose widget key is built
    # from the same label; two widgets with one key raise an error.
    switch_page_bttn(pages.browse_libs, label='Home', icon_='🏠', key='home2')