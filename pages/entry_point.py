import streamlit as st
# Don't import anything from this file, as it will run it again and re-run
# the current page.


page = st.navigation([
    st.Page('browse_libs.py', title='Browse Libraries', icon="🐐"),
    st.Page('browse_targets.py', title='Browse Targets', icon="🐐"),
    st.Page('browse_substrates.py', title='Browse Substrates', icon="🐐"),

    st.Page('new_lib.py', title='Add a New Library', icon="🐐"),
    st.Page('new_target.py', title='Add a New Target', icon="🐐"),
    st.Page('new_substrate.py', title='Add a New Substrate', icon="🐐"),

    st.Page('inspect_lib.py', title='Library', icon="🐐"),
    st.Page('inspect_target.py', title='Target', icon="🐐"),
    st.Page('inspect_substrate.py', title='Substrate', icon="🐐"),

    st.Page('library_added.py', title='New Library Added', icon="🐐"),
    st.Page('target_added.py', title='New Target Added', icon="🐐"),
    st.Page('substrate_added.py', title='New Substrate Added', icon="🐐"),

    st.Page('deleted_lib.py', title='Library Deleted', icon="🐐"),
    st.Page('deleted_target.py', title='Target Deleted', icon="🐐"),
    st.Page('deleted_sub.py', title='Substrate Deleted', icon="🐐"),

    st.Page('test.py', title='Test Page', icon="🐐"),
])

page.run()