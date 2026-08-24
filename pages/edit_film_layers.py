import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.edit_film_layers.sub_forms import RootForm
from components.general import init_page, \
    switch_to_submit_successful, current_params, sess
from logic.constants import IdType, CookieKeys as Ck
from logic.utils import save_cookies
from logic.lab_modelization.db_models import db, Film
from logic.page_list import pages

init_page(pages.edit_film_layers)

film_id = current_params()[IdType.FILM]
film: Film = Film.get_by_id(film_id)

st.set_page_config(layout='centered')

try:
    update_layers_form = RootForm(film)
    new_layers = update_layers_form.layers
    form_is_valid = update_layers_form.is_valid

    if st.button("Submit", disabled=not form_is_valid, type='primary'):
        sess[Ck.LAST_EMAIL_USED] = film.made_by_email
        for old_layer in film.layers:
            old_layer.delete_with_parts()

        with db.atomic():
            for new_layer in new_layers:
                new_layer.save_with_dependent()

        save_cookies()
        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=film.library.id,
        )


except PausePageRun:
    pass
