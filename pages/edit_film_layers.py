import streamlit as st

from components.forms.edit_film_layers.sub_forms import RootForm
from components.forms.shared2 import PausePageRun
from logic.constants import REDIRECT_PATH_URL_KEY, ID_KEY_URL_KEY, \
    ID_VALUE_URL_KEY, FILM_ID_URL_KEY, \
    LIB_ID_URL_KEY
from logic.functions import new_session_state, save_cookies
from logic.lab_modelization.db_models import db, Film
from logic.page_list import pages

film_id = st.query_params[FILM_ID_URL_KEY]
film: Film = Film.get_by_id(film_id)

sess = new_session_state(pages.edit_film_layers)
st.set_page_config(layout='centered')

try:
    update_layers_form = RootForm(film)
    new_layers = update_layers_form.layers
    form_is_valid = update_layers_form.is_valid

    if st.button("Submit", disabled=not form_is_valid, type='primary'):
        for old_layer in film.layers:
            old_layer.delete_instance(recursive=True)

        with db.atomic():
            for new_layer in new_layers:
                new_layer.save_with_dependent()

        save_cookies(sess)
        st.switch_page(
            pages.submission_successful,
            query_params={
                REDIRECT_PATH_URL_KEY: pages.inspect_lib.url_path,
                ID_KEY_URL_KEY: LIB_ID_URL_KEY,
                ID_VALUE_URL_KEY: film.library.id,
            }
        )


except PausePageRun:
    pass