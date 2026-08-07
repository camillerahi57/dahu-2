import streamlit as st
from PIL import Image
from streamlit import switch_page

from components.streamlit_tools import init_page, switch_button, \
    switch_to_submit_successful
from logic.components import inspect_page_header
from logic.constants import IdType
from logic.functions import email_html, extensive_date_str
from logic.lab_modelization.db_models import Target, DeteriorationState
from logic.math_tools import get_constrained_size
from logic.page_list import pages



init_page(pages.inspect_target)


def main_page():
    from components.streamlit_tools import current_params
    target_id = current_params()[IdType.TARGET]
    target: Target = Target.get_by_id(target_id)

    st.set_page_config(layout="wide", page_title=target.label)
    on_delete = get_on_delete_callback(target)
    # on_edit = get_target_edit_callback(target)

    inspect_page_header('Target', target.label, on_delete)

    show_target_info(target)
    switch_button(pages.edit_target, label="✏️ Edit base info",
              q_params={IdType.TARGET: str(target.id)})

    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader('Most Recent Deterioration State', width='content')
        # if st.button('➕ Add New State'):
        #     query_params = {IdType.TARGET: target_id}
        #     st.switch_page('new_deterioration_state.py',
        #                    query_params=query_params)
        switch_button(pages.new_state,
                      label='➕ Add New State',
                      q_params={IdType.TARGET: target_id})

    states = target.old_to_recent_states()
    last_state = states[-1]
    show_state(last_state, len(states))

    if len(states) > 1:
        st.divider()
        st.subheader('Deterioration History:')
        for state in reversed(states[:-1]):
            show_state(state, len(states))


def show_target_info(target: Target):
    with st.container(border=True):
        email = email_html(target.made_by_email)
        date_str = extensive_date_str(target.made_on)
        with st.container(horizontal=True, vertical_alignment="center"):
            st.write(f"Made on **{date_str}** by **{email}**.",
                     unsafe_allow_html=True)
            if target.previous_version is not None:
                previous: Target = target.previous_version
                st.write("Based on previous target:")
                # if st.button(previous.label, type='tertiary',
                #              key='previous'):
                #     switch_page(
                #         pages.inspect_target,
                #         query_params={IdType.TARGET: f'{previous.id}'}
                #     )
                switch_button(pages.inspect_target,
                              label=previous.label,
                              q_params={IdType.TARGET: f'{previous.id}'},
                              type_='tertiary', key='previous')
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
        img = Image.open(photo)
        w, h = get_constrained_size(img.width, img.height, 450, 450)
        st.image(photo, width=w, clamp=True)
        st.plotly_chart(state.to_figure(), width=300,
                        key=f'state_plot_{state.id}')


def show_state(state: DeteriorationState, state_count: int):
    with st.container(horizontal=True, vertical_alignment="center",
                      horizontal_alignment='center', border=True,
                      width='content'):
        with st.container():
            show_state_info(state)
            with st.container(horizontal=True, vertical_alignment="center"):
                # if st.button("✏️ Edit State",
                #              key=f'state_edit_{state.id}'):
                #     params = {IdType.STATE: f'{state.id}'}
                #     st.switch_page(pages.edit_state, query_params=params)
                switch_button(pages.edit_state,
                              label="✏️ Edit State",
                              q_params={IdType.STATE: f'{state.id}'},
                              key=f'state_edit_{state.id}')
                if state_count > 1:
                    if st.button("❌ Delete State",
                                 key=f'state_del_{state.id}'):
                        confirm_state_deletion_dialog(state)
        display_target_state(state)


def show_state_info(state: DeteriorationState):
    email = email_html(state.made_by_email)
    date_str = extensive_date_str(state.date)
    comment = state.comment if state.comment else "_empty_"
    with (st.container(width='content')):
        st.subheader(date_str)
        st.divider(width=1)
        st.write(f"**Updated by:** {email}", unsafe_allow_html=True)
        calib = state.calibration_factor_comment
        if not calib:
            calib = "*empty*"
        st.write(f"**Calibration factor:**  {calib}")
        with st.container(width=300):
            st.write(f"**Comment:** {comment}")


def dependent_lib_error(target_: Target):
    libs = target_.libraries()
    markdown = (f"The target cannot be deleted because {len(libs)} "
                f"libraries depend on it:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.label}]({lib_.url})"
    st.error(markdown)


@st.dialog(title="Confirm")
def confirm_deletion_dialog(target_: Target):
    st.error(f"Are you sure you want to **permanently** delete the "
             f"target **\"{target_.label}\"**?")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('Yes', key=f"target_confirm_{target_.id}"):
            target_.delete_instance(recursive=True)
            # st.switch_page('deleted_target.py')
            switch_to_submit_successful(pages.browse_targets)


def get_on_delete_callback(target: Target):
    def on_delete():
        if target.can_be_deleted():
            confirm_deletion_dialog(target)
        else:
            dependent_lib_error(target)

    return on_delete


def get_target_edit_callback(target: Target):
    params = {IdType.TARGET: str(target.id)}
    edit_page = pages.edit_target
    return lambda: st.switch_page(edit_page, query_params=params)


@st.dialog(title="Confirm")
def confirm_state_deletion_dialog(state: DeteriorationState):
    st.error(f"Are you sure you want to **permanently** delete the "
             f"the **{extensive_date_str(state.date)}** state?")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('Yes', key=f'state_confirm_{state.id}'):
            state.delete_instance(recursive=True)
            st.rerun()


main_page()
