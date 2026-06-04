import streamlit as st

from components.forms.new_target.sub_forms import BasicInfoForm
from components.forms.shared2 import StopPageLoad
from logic.constants import CookieKeys as Ck, TARGET_ID_URL_KEY, \
    REDIRECT_PATH_URL_KEY, ID_KEY_URL_KEY, ID_VALUE_URL_KEY
from logic.functions import load_session_state, save_cookies
from logic.lab_modelization.db_models import db, Target
from logic.page_list import pages

target_id = st.query_params[TARGET_ID_URL_KEY]
old_target: Target = Target.get_by_id(target_id)

sess = load_session_state(pages.edit_target)
st.set_page_config(layout='centered')

try:
    root_form = BasicInfoForm(default_target=old_target)
    # Copying the ID to replace the old one:
    new_target = root_form.to_target(id_=old_target.id)

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        sess[Ck.LAST_EMAIL_USED] = new_target.made_by_email

        with db.atomic():
            new_target.save()

        save_cookies(sess)
        st.switch_page(
            pages.submission_successful,
            query_params={
                REDIRECT_PATH_URL_KEY: pages.inspect_target.url_path,
                ID_KEY_URL_KEY: TARGET_ID_URL_KEY,
                ID_VALUE_URL_KEY: new_target.id,
            }
        )

except StopPageLoad:
    pass

