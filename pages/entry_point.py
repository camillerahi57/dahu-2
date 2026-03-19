import streamlit as st
# Don't import anything from this file, as it will run it again and re-run the current page.


page = st.navigation([
    st.Page('browse_libs.py', title='Browse Libraries', icon=":material/edit:"),
    st.Page('browse_targets.py', title='Browse Targets', icon=":material/edit:"),
    st.Page('browse_substrates.py', title='Browse Substrates', icon=":material/edit:"),

    st.Page('new_lib.py', title='Add a New Library', icon=":material/edit:"),
    st.Page('new_target.py', title='Add a New Target', icon=":material/edit:"),

    st.Page('inspect_lib.py', title='Inspect a Library', icon=":material/edit:"),

    st.Page('library_added.py', title='New Library Added', icon=":material/edit:"),
    st.Page('target_added.py', title='New Target Added', icon=":material/edit:"),

    st.Page('test.py', title='Test Page', icon=":material/edit:"),
])

page.run()