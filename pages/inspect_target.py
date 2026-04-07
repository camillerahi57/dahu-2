import datetime

from streamlit import columns
import streamlit as st

from logic.constants import TARGET_ID_URL_KEY
from logic.db_schema import Target
from logic.functions import get_email_user_name


target_id = st.query_params[TARGET_ID_URL_KEY]
target: Target = Target.get_by_id(target_id)

st.set_page_config(layout="wide", page_icon='🎯', page_title=target.physical_name)

col1, col2, col3 = st.columns([5, 20, 60])
with col1:
    st.write('**TARGET**')
with col2:
    st.subheader(target.physical_name)
# with col3:
#     delete button


col1, col2 = columns([40, 60])

with col1:
    with st.container(border=True):
        st.image(target.photo_path())
        st.plotly_chart(target.to_plotly_figure())

with col2:
    with st.container(border=True):
        email_html = f'<a href="mailto:{target.made_by_email}">{target.made_by_email}</a>'
        date_str = datetime.date(target.made_at.year, target.made_at.month, target.made_at.day).strftime("%B %d, %Y")
        experimenter = get_email_user_name(target.made_by_email)
        st.write(f"Made on **{date_str}** by **{email_html}**.", unsafe_allow_html=True)
        st.write(f"**Comment:** {target.comment if target.comment else '*No comment.*'}")