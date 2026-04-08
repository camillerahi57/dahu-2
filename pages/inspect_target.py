import datetime

import streamlit as st
from streamlit import columns

from logic.constants import TARGET_ID_URL_KEY
from logic.db_schema import Target
from logic.functions import get_email_user_name


def dependent_lib_error(target_: Target):
    libs = target_.libraries()
    markdown = (f"The target cannot be deleted because {len(libs)} "
                f"libraries depend on it:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.name}]({lib_.get_url()})"
    st.error(markdown)


@st.dialog(title="Confirm")
def confirm_deletion_dialog(target_: Target):
    st.error(f"Are you sure you want to **permanently** delete the "
             f"target **\"{target_.physical_name}\"**?")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('Yes'):
            target_.delete_instance()
            st.switch_page('deleted_target.py')


target_id = st.query_params[TARGET_ID_URL_KEY]
target: Target = Target.get_by_id(target_id)

st.set_page_config(layout="wide", page_title=target.physical_name)

col1, col2 = st.columns(2)
with col1:
    with st.container(horizontal=True, vertical_alignment="center"):
        st.write('**TARGET**')
        st.subheader(target.physical_name)
with col2:
    with st.container(horizontal=True, horizontal_alignment='right'):
        if st.button('Delete 🗑️'):
            if target.can_be_deleted():
                confirm_deletion_dialog(target)
            else:
                dependent_lib_error(target)

# TODO vérifier que ça marche

col1, col2 = columns([40, 60])

with col1:
    with st.container(border=True):
        st.image(target.photo_path())
        st.plotly_chart(target.to_plotly_figure())

with col2:
    with st.container(border=True):
        email_html = (f'<a href="mailto:{target.made_by_email}">'
                      f'{target.made_by_email}</a>')
        date_str = datetime.date(target.made_at.year, target.made_at.month,
                                 target.made_at.day).strftime("%B %d, %Y")
        experimenter = get_email_user_name(target.made_by_email)
        st.write(f"Made on **{date_str}** by **{email_html}**.",
                 unsafe_allow_html=True)
        st.write(f"**Comment:** {target.comment if target.comment 
        else '*No comment.*'}")
