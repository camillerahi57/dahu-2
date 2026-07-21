import streamlit as st

from components.forms.new_film_modif.sub_forms import RootForm
from components.forms.shared2 import PausePageRun
from logic.constants import CookieKeys as Ck, \
    FILM_ID_URL_KEY, REDIRECT_PATH_URL_KEY, ID_KEY_URL_KEY, ID_VALUE_URL_KEY, \
    LIB_ID_URL_KEY, SessionKeys as Sk
from logic.functions import new_session_state, save_cookies
from logic.lab_modelization.db_models import (
    db, Film)
from logic.page_list import pages

sess = new_session_state(pages.new_film_modif)
st.set_page_config(layout="centered")

film_id = target_id = st.query_params[FILM_ID_URL_KEY]
film: Film = Film.get_by_id(film_id)
st.session_state[Sk.CURRENT_FILM] = film

try:
    root_form = RootForm(None, film)
    film_modif = root_form.film_modif

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        sess[Ck.LAST_EMAIL_USED] = film_modif.made_by_email

        with db.atomic():
            film_modif.save_with_dependent()

        save_cookies(sess)
        st.switch_page(
            page=pages.submission_successful,
            query_params={
                REDIRECT_PATH_URL_KEY: pages.inspect_lib.url_path,
                ID_KEY_URL_KEY: LIB_ID_URL_KEY,
                ID_VALUE_URL_KEY: film.library.id,
            }
        )

except PausePageRun:
    pass
