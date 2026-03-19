from random import shuffle

import streamlit as st

from logic.db_schema import Experimenter, Library, Characterization, db

st.title('New library')

possible_methods = ["MOKE", "EDX", "X-ray", "Profilo"]
shuffle(possible_methods)
possible_makers = ["William", "Pierre"]
shuffle(possible_makers)

lib_name = st.text_input("Library name:", value='Nd|Ce|B')
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
    # We use that instead of "Experimenter(full_name=full_name, [...]" to have IDE auto-completion and refactorization.
    experimenter = Experimenter.new(full_name=full_name, email_address=email)
    library = Library.new(name=lib_name, comment=comment, made_at=made_at)
    charac = Characterization.new(name=method, experimenter=experimenter, library=library)

    with db.atomic():
        experimenter.save()
        library.save()
        charac.save()

    st.switch_page('library_added.py')