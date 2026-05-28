import streamlit as st

from components.forms.edit_target.sub_forms import BasicInfoForm
from components.forms.shared2 import StopPageLoad
from logic.constants import CookieKeys as Ck, TARGET_ID_URL_KEY
from logic.functions import load_session_state, save_session_state
from logic.lab_modelization.db_models import db, Target
from logic.page_list import PageEnum

target_id = st.query_params[TARGET_ID_URL_KEY]
target: Target = Target.get_by_id(target_id)

sess = load_session_state(PageEnum.edit_target)
st.set_page_config(layout='centered')

try:
    root_form = BasicInfoForm(updated_target=target)
    target = root_form.to_target(updated_target=target)

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        sess[Ck.LAST_EMAIL_USED] = target.made_by_email

        with db.atomic():
            target.save()
            save_session_state(sess)
        st.switch_page('submission_successful.py')

except StopPageLoad:
    pass

