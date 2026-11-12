"""Page for editing the targets used by a film and its layers.

The film is chosen by the `film_id` query parameter (a `name=value`
pair after the `?` of the URL, see `IdType.FILM`). The form is
`edit_film_layers.sub_forms.RootForm`, prefilled from the film. On
submit, all the old layers are deleted with their parts, then the new
ones are saved with theirs (they get new ids). The user is then sent to
the library's page.
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.edit_film_layers.sub_forms import RootForm
from components.general import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Film
from logic.page_list import pages

init_page(pages.edit_film_layers)

film_id = current_params()[IdType.FILM]
film: Film = Film.get_by_id(film_id)

st.set_page_config(layout='centered')

try:
    # Raises `PausePageRun` while the layers are invalid, so the
    # button below only appears once they are valid.
    update_layers_form = RootForm(film)
    new_layers = update_layers_form.layers
    form_is_valid = update_layers_form.is_valid

    if st.button("Submit", disabled=not form_is_valid, type='primary'):
        # TODO The old layers are deleted before, and
        #   outside, the `with db.atomic():` (a transaction: DB writes
        #   that either all succeed or are all cancelled). If saving the
        #   new layers fails, the film is left with no layers.
        for old_layer in film.layers:
            old_layer.delete_with_parts()

        with db.atomic():
            for new_layer in new_layers:
                new_layer.save_with_dependent()

        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=film.library.id,
        )


except PausePageRun:
    pass
