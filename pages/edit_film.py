import streamlit as st

from components.forms.new_library.sub_forms import FilmInfoForm
from components.forms.shared2 import PausePageRun
from logic.constants import REDIRECT_PATH_URL_KEY, ID_KEY_URL_KEY, \
    ID_VALUE_URL_KEY, FILM_ID_URL_KEY, \
    LIB_ID_URL_KEY
from logic.functions import new_session_state, save_cookies
from logic.lab_modelization.db_models import db, Film
from logic.page_list import pages

film_id = st.query_params[FILM_ID_URL_KEY]
old_film: Film = Film.get_by_id(film_id)

sess = new_session_state(pages.edit_film)
st.set_page_config(layout='centered')

try:
    root_form = FilmInfoForm(old_film)
    # Copying the ID to keep the old one and update it:
    new_film = root_form.to_film(old_film.library, id_=old_film.id)

    if st.button("Submit", disabled=not root_form.is_valid, type='primary'):
        with db.atomic():
            new_film.save()

        save_cookies(sess)
        st.switch_page(
            pages.submission_successful,
            query_params={
                REDIRECT_PATH_URL_KEY: pages.inspect_lib.url_path,
                ID_KEY_URL_KEY: LIB_ID_URL_KEY,
                ID_VALUE_URL_KEY: new_film.library.id,
            }
        )

except PausePageRun:
    pass