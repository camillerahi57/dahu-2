"""Page showing one sputtering target and its deterioration history.

The target is chosen by the `target_id` query parameter (a
`name=value` pair after the `?` of the URL, see `IdType.TARGET`). The
page shows the base info, then each `DeteriorationState` (photo and
patches), most recent first. From here the user can edit, archive,
delete the target, and add, edit or delete states.
"""
import streamlit as st
from PIL import Image

from components.general import init_page, switch_page_bttn, \
    switch_to_submit_successful, email_html, extensive_date_str, icon
from components.inspection import inspect_page_header
from logic.constants import IdType
from logic.lab_modelization.db_models import Target, DeteriorationState
from logic.math_tools import get_constrained_size
from logic.page_list import pages

init_page(pages.inspect_target)


def main_page():
    """Draw the whole page.

    Side effects: the Archive / Unarchive buttons save the target
    (writes an `AppLog` row) and rerun the script (Streamlit runs the
    page script again from the top to redraw it).
    """
    from components.general import current_params
    target_id = current_params()[IdType.TARGET]
    target: Target = Target.get_by_id(target_id)

    st.set_page_config(layout="wide", page_title=target.label)
    if target.is_archived:
        st.warning("📦 Archived", width=10_000)
    on_delete = get_on_delete_callback(target)

    inspect_page_header('Target', target.label, on_delete)
    if not target.is_archived:
        with st.container(horizontal_alignment='right'):
            if st.button("Archive 📦"):
                archive_dialog(target)
    else:
        with st.container(horizontal_alignment='right'):
            if st.button("Unarchive 📤"):
                target.is_archived = False
                target.save()
                st.rerun()

    show_base_info(target)
    switch_page_bttn(pages.edit_target, label="Edit base info", icon_='✏️',
                     q_params={IdType.TARGET: str(target.id)})

    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader('Most Recent Deterioration State', width='content')
        switch_page_bttn(pages.new_state,
                         label='Add New State', icon_=icon('add_2'),
                         q_params={IdType.TARGET: target_id})

    # A target always gets a first state when it is created, and the
    # last state can't be deleted (see `show_state`), so `states` is
    # never empty.
    states = target.old_to_recent_states()
    last_state = states[-1]
    show_state(last_state, len(states))

    if len(states) > 1:
        st.divider()
        st.subheader('Deterioration History:')
        for state in reversed(states[:-1]):
            show_state(state, len(states))


def show_base_info(target: Target):
    """Draw the box with who made the target, when, and its comments.

    Also links to the previous version of the target, if any, and to
    the targets made from this one (`next_versions`).

    Args:
        target: The target shown on the page.
    """
    with st.container(border=True):
        email = email_html(target.made_by_email)
        date_str = extensive_date_str(target.made_on)
        with st.container(horizontal=True, vertical_alignment="center"):
            st.write(f"Made on **{date_str}** by **{email}**.",
                     unsafe_allow_html=True)
            if target.previous_version:
                previous: Target = target.previous_version
                st.write("Based on previous target:")
                switch_page_bttn(pages.inspect_target,
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
        with st.container(horizontal=True, vertical_alignment="center"):
            if target.next_versions:
                st.write(f"**Targets base on the current one:**")
            # This page always has a query parameter, so
            # `switch_page_bttn` draws HTML links and ignores `key`.
            for t in target.next_versions:
                switch_page_bttn(
                    pages.inspect_target, label=t.label,
                    q_params={IdType.TARGET: t.id}, key=str(t.id)
                )


def display_target_state(state: DeteriorationState):
    """Draw the state's photo next to a plot of its patches.

    The photo is shrunk to fit in 450 × 450 pixels. If its file is
    missing from `user_data/`, a message replaces it.

    Args:
        state: The deterioration state to draw.
    """
    photo = state.photos[0].get_path()
    with st.container(horizontal=True, vertical_alignment="center",
                      width='content'):
        try:
            img = Image.open(photo)
            w, h = get_constrained_size(img.width, img.height, 450, 450)
            st.image(photo, width=w, clamp=True)
        except FileNotFoundError:
            st.write("_Photo file missing_")
        # Each state has its own plot, so each needs its own widget key
        # (the name Streamlit uses to tell widgets apart).
        st.plotly_chart(state.to_figure(), width=300,
                        key=f'state_plot_{state.id}')


def show_state(state: DeteriorationState, state_count: int):
    """Draw one state: its info, Edit / Delete buttons, photo and plot.

    Args:
        state: The deterioration state to draw.
        state_count: Number of states of the target. The Delete button
            is hidden when it is 1, so a target always keeps a state.
    """
    with st.container(horizontal=True, vertical_alignment="center",
                      horizontal_alignment='center', border=True,
                      width='content'):
        with st.container():
            show_state_info(state)
            with st.container(horizontal=True, vertical_alignment="center"):
                switch_page_bttn(pages.edit_state,
                                 label="Edit State", icon_='✏️',
                                 q_params={IdType.STATE: f'{state.id}'},
                                 key=f'state_edit_{state.id}')
                if state_count > 1:
                    if st.button("❌ Delete State",
                                 key=f'state_del_{state.id}'):
                        confirm_state_deletion_dialog(state)
        display_target_state(state)


def show_state_info(state: DeteriorationState):
    """Draw the state's date, author, calibration factor and comment.

    Args:
        state: The deterioration state to describe.
    """
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
    """Explain why the target can't be deleted, with library links.

    Shown instead of the confirmation dialog when film layers were
    deposited with the target.

    Args:
        target_: The target the user tried to delete.
    """
    libs = target_.libraries()
    markdown = (f"The target cannot be deleted because {len(libs)} "
                f"librarie(s) depend on it:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.label}]({lib_.url})"
    st.error(markdown)


@st.dialog(title="Confirm")
def confirm_deletion_dialog(target_: Target):
    """Ask for confirmation, then delete the target and its states.

    Opens as a dialog (a pop-up window drawn over the page). If other
    targets were made from this one, warns that they are kept but lose
    their link to it: the DB sets their `previous_version` to NULL
    (`on_delete='SET NULL'`). On confirmation, deletes the target, its
    states, patches and photos (rows and files, writes `AppLog` rows)
    and goes to the "submission successful" page.

    Args:
        target_: The target to delete.
    """
    if target_.next_versions:
        next_versions = target_.next_versions
        st.error(
            f"**{len(next_versions)}** other target(s) are built based on "
            f"this one.\n\n"
            f"Targets based one the deleted one will not be "
            f"deleted, but the information that they were based on a "
            f"previous target will be lost."
        )
        st.write(f"**Concerned targets:**")
        with st.container(horizontal=True, vertical_alignment="center"):
            for target in next_versions:
                switch_page_bttn(
                    pages.inspect_target, label=target.label,
                    q_params={IdType.TARGET: target.id}, key=str(target.id)
                )
    else:
        st.error(f"Are you sure you want to **permanently** delete the target "
               f"**\"{target_.label}\"**?")
    st.divider()
    if st.button('Confirm', key=f"target_confirm_{target_.id}"):
        target_.delete_with_parts()
        switch_to_submit_successful(pages.browse_targets)


def get_on_delete_callback(target: Target):
    """Build the function called when "Delete Target" is clicked.

    `inspect_page_header` calls its `on_delete` with no argument, so the
    target is captured in a closure (a function defined inside another
    one, which remembers the outer function's variables).

    Args:
        target: The target shown on the page.

    Returns:
        A function with no argument that opens the confirmation dialog,
        or shows an error if the target is used by some library.
    """
    def on_delete():
        """Open the deletion dialog, or explain why deletion is refused.
        """
        if target.can_be_deleted():
            confirm_deletion_dialog(target)
        else:
            dependent_lib_error(target)

    return on_delete


@st.dialog(title="Confirm")
def confirm_state_deletion_dialog(state: DeteriorationState):
    """Ask for confirmation, then delete one deterioration state.

    Opens as a dialog. On confirmation, deletes the state with its
    patches and photo (rows and file, writes `AppLog` rows) and reruns
    the page.

    Args:
        state: The state to delete.
    """
    st.error(f"Are you sure you want to **permanently** delete the "
             f"the **{extensive_date_str(state.date)}** state?")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('Yes', key=f'state_confirm_{state.id}'):
            state.delete_with_parts()
            st.rerun()


@st.dialog(title='Archive?')
def archive_dialog(target: Target):
    """Ask for confirmation, then mark the target as archived.

    Opens as a dialog. Archived targets are hidden on the browse page
    unless "Show archived" is checked. Saving writes an `AppLog` row.

    Args:
        target: The target to archive.
    """
    st.write("This will not delete the target, no data will be lost.")
    st.write("The target will simply be marked as 'Archived'.")
    if st.button("Confim"):
        target.is_archived = True
        target.save()
        st.rerun()


main_page()
