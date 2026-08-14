import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_film_modif.sub_forms import RootForm
from components.streamlit_tools import sess, init_page, \
    switch_to_submit_successful, current_params
from logic.constants import CookieKeys as Ck, \
    SessionKeys as Sk, IdType
from logic.functions import save_cookies
from logic.lab_modelization.db_models import (
    db, Film)
from logic.page_list import pages

init_page(pages.new_film_modif)

st.set_page_config(layout="centered")

film_id = target_id = current_params()[IdType.FILM]
film: Film = Film.get_by_id(film_id)
st.session_state[Sk.CURRENT_FILM] = film

try:
    root_form = RootForm(None, film)
    film_modif = root_form.film_modif

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        sess[Ck.LAST_EMAIL_USED] = film_modif.made_by_email

        with db.atomic():
            film_modif.save_with_dependent()

        save_cookies()
        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=film.library.id,
        )

except PausePageRun:
    pass
