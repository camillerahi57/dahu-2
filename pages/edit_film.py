import streamlit as st

from components.forms.new_library.sub_forms import FilmInfoForm
from components.forms.shared2 import PausePageRun
from components.streamlit_tools import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import IdType
from logic.functions import save_cookies
from logic.lab_modelization.db_models import db, Film
from logic.page_list import pages

init_page(pages.edit_film)

film_id = current_params()[IdType.FILM]
old_film: Film = Film.get_by_id(film_id)

st.set_page_config(layout='centered')


try:
    root_form = FilmInfoForm(old_film)
    # Copying the ID to keep the old one and update it:
    new_film = root_form.to_film(old_film.library, id_=old_film.id)

    if st.button("Submit", disabled=not root_form.is_valid, type='primary'):
        with db.atomic():
            new_film.save()

        save_cookies()
        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=new_film.library.id,
        )

except PausePageRun:
    pass