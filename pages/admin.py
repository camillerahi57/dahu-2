"""Admin page: link to the logs, XLSX export of the whole database, and
restoration of the app state from a Restic snapshot.

A snapshot is a saved copy of the whole `user_data/` folder (database
and uploaded files) taken by Restic, the backup program. Restoring one
brings every user's data back to that moment and deletes the later
snapshots (see `Snapshot.restore`). It is protected by the password in
the `dahu_admin_password` environment variable.

A dialog is a pop-up window drawn by a function decorated with
`@st.dialog`; it opens when the function is called and closes on the
next rerun (Streamlit re-executing the page script).
"""
import os
from datetime import datetime
from time import sleep

import streamlit as st

from components.general import init_page, compact_datetime_str, \
    datetime_sentence, switch_page_bttn
from logic.app_restoration import Snapshot
from logic.constants import SessionKeys as Sk
from logic.global_variables import sess
from logic.meta_data_init import app_metadata
from logic.page_list import pages
from logic.utils import database_to_excel_file_bytes

init_page(pages.admin)
st.set_page_config(layout='centered')


@st.dialog('ARE YOU SURE YOU WANT TO RESET ALL DATA TO THIS POINT?')
def restore_warning_dialog(snap: Snapshot):
    """Ask for the admin password before restoring a snapshot.

    The Confirm button stays disabled until the password is right. On
    confirm, the snapshot is stored in the session state (Streamlit's
    per-tab dictionary that survives reruns) and the page reruns, which
    closes this dialog; `body` then opens `restore_process_dialog`
    (Streamlit allows only one open dialog at a time).

    Side effect: writes `Sk.SNAP_TO_RESTORE` in the session state.

    Args:
        snap: The snapshot chosen on the page.
    """
    time_str = datetime_sentence(snap.time)
    msg = f"""The state of Dahu DB will be reset to:\n\n**{time_str}**."""
    st.error(msg)
    entered_password = st.text_input("Dahu DB admin password:",
                                     type='password')
    correct_password = entered_password == os.environ['dahu_admin_password']
    if st.button('⚠️ **Confirm** ⚠️', disabled=not correct_password):
        sess[Sk.SNAP_TO_RESTORE] = snap
        st.rerun()


@st.dialog('Please wait')
def restore_process_dialog(snap: Snapshot):
    """Restore a snapshot while showing a progress bar, then rerun.

    Opened by `body` on the rerun that follows the confirmation in
    `restore_warning_dialog`.

    Side effects: replaces `user_data/` (DB and files) with the
    snapshot's content and deletes the later snapshots (see
    `Snapshot.restore`, which also writes `AppMetadata` and, on error,
    `AppLog`); removes `Sk.SNAP_TO_RESTORE` from the session state.

    Args:
        snap: The snapshot to restore.

    Raises:
        RuntimeError: If Restic fails (raised by `Snapshot.restore`).
    """
    # Removed first so that the next rerun does not restore again.
    # `pop` (not `del`): if the restore raises, the dialog fragment
    # reruns and the key is already gone, which would hide the real error
    # behind a KeyError.
    sess.pop(Sk.SNAP_TO_RESTORE, None)
    # `Snapshot.restore` closes the DB connection after Restic runs and
    # reloads `app_metadata` from the restored DB.
    snap.restore()
    st.success(f"**Dahu DB data was restored successfully.**")
    # Leaves the message on screen for 5 s; the rerun closes the dialog.
    sleep(5)
    st.rerun()


def snapshot_row(snap: Snapshot):
    """Draw one restore point: its date and a Restore button.

    The button opens `restore_warning_dialog`. Its widget key (the name
    Streamlit uses to tell widgets apart) includes the snapshot id,
    since every row has a button with the same label.

    Args:
        snap: The snapshot to show.
    """
    with st.container(border=True, horizontal=True,
                      horizontal_alignment='distribute',
                      vertical_alignment='center',
                      width=500):
        st.write(f'**{datetime_sentence(snap.time)}**')
        if st.button('Restore', key='restore'+snap.id):
            restore_warning_dialog(snap)


def body():
    """Draw the page.

    Starts the pending restore if one was confirmed on the previous run,
    then draws the logs link, the XLSX download, the warning and the
    list of restore points (newest first) with the next backup time.

    Side effects: runs `restic snapshots` on every run (see
    `Snapshot.list_available`), and may restore a snapshot (see
    `restore_process_dialog`).
    """
    if Sk.SNAP_TO_RESTORE in sess and sess[Sk.SNAP_TO_RESTORE]:
        snap = sess[Sk.SNAP_TO_RESTORE]
        restore_process_dialog(snap)

    st.subheader("Internal logs")
    switch_page_bttn(pages.view_logs, label='View logs', key='logs')

    st.header("Explore Database")

    # The file is built on every run of the page, not only on click:
    # `st.download_button` needs the bytes before the button is drawn.
    st.download_button(
        'Download as XLSX',
        data=database_to_excel_file_bytes(),
        file_name=f'dahu_2_db_{compact_datetime_str(datetime.now())}.xlsx'
    )

    st.divider()

    st.header("App State Restoration")

    warning_msg = """
    If you restore the app state back to a restoration point, all modifications 
    made after the date of the restoration point will be cancelled. This may 
    imply **data loss**, including:
    - created libraries, targets, film modifications, etc.
    - added library files
    - pictures
    - any other generated or uploaded file
    - any other change made in the database 
    
    Moreover, going back to a past restore point will **delete subsequent 
    restore points** (but not the selected restore point).
    
    **Restoration will affect data of all users.**
    """
    st.error(warning_msg, title="DANGER ZONE")

    st.write("Go back in time, restore app state (database and stored files) "
             "to a previous point in time. It will restore deleted data.")

    st.subheader("Available Restore Points")
    try:
        snapshots = Snapshot.list_available()
        if not snapshots:
            st.write('_No restore point available._')
        else:
            # Newest first, assuming Restic lists them oldest first.
            for snap in reversed(snapshots):
                snapshot_row(snap)
    # TODO `list_available` returns an empty list instead of raising when
    #  Restic fails.
    except RuntimeError as e:
        st.error(f"**Unable to list available restore points. "
                 f"Error message:**\n\n{e}")
    next_time = app_metadata.next_backup_at
    st.subheader(f"Next backup: {datetime_sentence(next_time)}.")

body()
