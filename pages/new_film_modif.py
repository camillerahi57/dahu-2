"""Page for recording a modification (annealing or etching) of a film.

The film is chosen by the `film_id` query parameter (a `name=value`
pair after the `?` of the URL, see `IdType.FILM`). The form is
`new_film_modif.sub_forms.RootForm`. On submit, the modification and
its subtype rows (annealing steps, or etching details) are saved in one
transaction (a group of DB writes that either all succeed or are all
cancelled), with an `AppLog` row for the modification. The user is
then sent to the film's library page.
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_film_modif.sub_forms import RootForm
from components.general import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import SessionKeys as Sk, IdType
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import (
    Film)
from logic.page_list import pages

init_page(pages.new_film_modif)

st.set_page_config(layout="centered")

# TODO target_id never used.
film_id = target_id = current_params()[IdType.FILM]
film: Film = Film.get_by_id(film_id)
# Read by the "previous film modification" field (see
# `get_options` in `new_film_modif/fields.py`). The library page sets it
# too, but `init_page` cleared it on arrival, so set it again here. The
# session state is a dictionary Streamlit keeps for each browser tab
# across reruns (the re-executions of the page after each click).
st.session_state[Sk.CURRENT_FILM] = film

try:
    # Raises `PausePageRun` until the whole form is valid, so the
    # button below only appears then.
    root_form = RootForm(None, film)
    film_modif = root_form.film_modif

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        with db.atomic():
            film_modif.save_with_dependent()

        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=film.library.id,
        )

except PausePageRun:
    pass
