"""Page for recording a characterization (e.g. an EDX) made on a film.

The film is chosen by the `film_id` query parameter (a `name=value`
pair after the `?` of the URL, see `IdType.FILM`). The form is
`new_charac.sub_forms.RootForm`. On submit, the data file is first
written to `user_data/` (it can be several GB, so this can take a
while), then the data file's row, the characterization and its subtype
rows (e.g. the EDX results per element) are saved in one transaction (a
group of DB writes that either all succeed or are all cancelled). The
file comes first so that the transaction, which locks the whole database
for the other users, stays short; if the transaction fails, the file is
deleted again. The user is then sent to the film's library page.

A characterization made on another film is not recorded here: the
library page adds a reference to it instead (see `CharacReference`).
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.new_charac.sub_forms import RootForm
from components.general import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Film
from logic.page_list import pages

init_page(pages.new_charac)

st.set_page_config(layout="centered")

film_id = current_params()[IdType.FILM]
film: Film = Film.get_by_id(film_id)

try:
    # Raises `PausePageRun` until a type is chosen.
    root_form = RootForm(film)

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        charac_file = root_form.charac_file
        with st.spinner('Saving the data file, please wait...'):
            charac_file.save_stream(root_form.file_stream)
            try:
                with db.atomic():
                    # The file row first: the charac needs its id.
                    charac_file.save()
                    root_form.charac.save_with_dependent()
            except BaseException:
                # No row points to the file: don't leave it on the disk.
                charac_file.get_path().unlink(missing_ok=True)
                raise

        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=film.library.id,
        )

except PausePageRun:
    pass
