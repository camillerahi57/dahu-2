import streamlit as st

from logic.components import inspect_page_header
from logic.constants import TARGET_ID_URL_KEY
from logic.functions import email_html, extensive_date_str, load_session_state
from logic.lab_modelization.db_models import Target, DeteriorationState
from logic.page_list import PageEnum


def main_page():
    page = PageEnum.inspect_target.value
    load_session_state(page)

    target_id = st.query_params[TARGET_ID_URL_KEY]
    target: Target = Target.get_by_id(target_id)

    st.set_page_config(layout="wide", page_title=target.physical_name)
    on_delete = get_on_delete_callback(target)
    on_edit = get_target_edit_callback(target)

    inspect_page_header('Target', target.physical_name, on_delete,
                        on_edit, page)

    show_target_info(target)
    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader('Current Deterioration State', width='content')
        if st.button('➕ Add New State'):
            query_params = {TARGET_ID_URL_KEY: target_id}
            st.switch_page('new_deterioration_state.py',
                           query_params=query_params)

    states = target.old_to_recent_states()
    last_state = states[-1]
    show_state(last_state)

    if len(states) > 1:
        st.divider()
        st.subheader('Deterioration History:')
        for state in reversed(states[:-1]):
            show_state(state)


def show_target_info(target: Target):
    with st.container(border=True):
        email = email_html(target.made_by_email)
        date_str = extensive_date_str(target.made_on)
        st.write(f"Made on **{date_str}** by **{email}**.",
                 unsafe_allow_html=True)
        comments = target.comments()
        if len(comments) > 0:
            st.write(f"**Comments:**")
            for date, comment in target.comments():
                st.write(f"- **[{date}]** {comment}")
        else:
            st.write(f"**Comments:** _empty_")


def display_target_state(state: DeteriorationState):
    photo = state.photo_path()
    with st.container(horizontal=True, vertical_alignment="center",
                      width='content'):
        st.image(photo, width=450, clamp=True)
        st.plotly_chart(state.to_figure(), width=300,
                        key=f'state_plot_{state.id}')


def show_state(state: DeteriorationState):
    with st.container(horizontal=True, vertical_alignment="center",
                      horizontal_alignment='center', border=True,
                      width='content'):
        with st.container():
            show_state_info(state)
            if st.button("❌ Delete State", key=f'state_del_{state.id}'):
                confirm_state_deletion_dialog(state)
        display_target_state(state)


def show_state_info(state: DeteriorationState):
    email = email_html(state.made_by_email)
    date_str = extensive_date_str(state.date)
    comment = state.comment if state.comment else "_empty_"
    with st.container(width='content'):
        st.subheader(date_str)
        st.write(f"**Updated by:** {email}", unsafe_allow_html=True)
        st.write(f"**Calibration factor:** {state.calibration_factor:g}")
        with st.container(width=300):
            st.write(f"**Comment:** {comment}")


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
        if st.button('Yes', key=f"target_confirm_{target_.id}"):
            target_.delete_instance()
            st.switch_page('deleted_target.py')


def get_on_delete_callback(target: Target):
    def on_delete():
        if target.can_be_deleted():
            confirm_deletion_dialog(target)
        else:
            dependent_lib_error(target)

    return on_delete


def get_target_edit_callback(target: Target):
    params = {TARGET_ID_URL_KEY: target.id}
    edit_page = PageEnum.edit_target.value
    return lambda: st.switch_page(edit_page, query_params=params)


@st.dialog(title="Confirm")
def confirm_state_deletion_dialog(state: DeteriorationState):
    st.error(f"Are you sure you want to **permanently** delete the "
             f"the **{extensive_date_str(state.date)}** state?")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('Yes', key=f'state_confirm_{state.id}'):
            state.delete_instance()
            st.rerun()


main_page()
