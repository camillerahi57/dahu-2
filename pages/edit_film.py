"""Page for editing a film's label, deposition date, author and
substrate.

The film is chosen by the `film_id` query parameter (a `name=value`
pair after the `?` of the URL, see `IdType.FILM`). Its layers are
edited on the "edit film layers" page. On submit, the film row is
updated in place, keeping its id and library, and the user is sent to
the library's page.
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_library.sub_forms import FilmInfoForm
from components.general import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Film
from logic.page_list import pages

init_page(pages.edit_film)

film_id = current_params()[IdType.FILM]
old_film: Film = Film.get_by_id(film_id)

st.set_page_config(layout='centered')


try:
    root_form = FilmInfoForm(old_film)
    # Copying the ID to keep the old one and update it:
    # (`save()` on an object that has an id updates that row.)
    # `to_film` raises `PausePageRun` while the form is invalid, so the
    # button below only appears once it is valid.
    new_film = root_form.to_film(old_film.library, id_=old_film.id)

    if st.button("Submit", disabled=not root_form.is_valid, type='primary'):
        with db.atomic():
            new_film.save()

        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=new_film.library.id,
        )

except PausePageRun:
    pass