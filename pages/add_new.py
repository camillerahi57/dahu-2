from random import shuffle

import streamlit as st

from entry_point import DahuPages
from tools.db_schema import Experimenter, Library, CharacMethod

st.title('New library')

possible_methods = ["MOKE", "EDX", "X-ray", "Profilo"]
shuffle(possible_methods)
possible_makers = ["William", "Pierre"]
shuffle(possible_makers)

lib_name = st.text_input("Library name:", value='Nd|Ce|Br')
made_at = st.datetime_input("Made at:")
method = st.selectbox("Characterisation Method:", possible_methods)
comment = st.text_input("Comment:", value='Sample made with love.')
full_name = st.text_input("Experimenter full name:", value=possible_makers[0])
email = st.text_input("Experimenter email address:", value=possible_makers[0].lower()+'@cnrs.fr')

valid_form = (
    len(lib_name) > 0
    and len(comment) > 0
    and made_at is not None
    and len(full_name) > 0
    and len(email) > 0
    and method in possible_methods
)

if st.button("Submit", disabled=not valid_form):
    experimenter_kwargs = {
        Experimenter.full_name.name: full_name,
        Experimenter.email_address.name: email,
    }
    # We use that instead of "Experimenter(full_name=full_name, [...]" to have IDE auto-completion and refactorization.
    experimenter = Experimenter(**experimenter_kwargs)

    library_kwargs = {
        Library.name.name: lib_name,
        Library.comment.name: comment,
        Library.made_at.name: made_at,
    }
    library = Library(**library_kwargs)

    charac_kwargs = {
        CharacMethod.name.name: method,
        CharacMethod.experimenter.name: experimenter,
        CharacMethod.library.name: library,
    }
    charac = CharacMethod(**charac_kwargs)

    experimenter.save()
    library.save()
    charac.save()

    st.switch_page(DahuPages.library_added)