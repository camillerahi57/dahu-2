from datetime import datetime
from time import sleep

import streamlit as st

from components.general import init_page, sess, app_metadata, \
    compact_datetime_str, datetime_sentence
from logic.app_restoration import Snapshot
from logic.constants import SessionKeys as Sk
from logic.lab_modelization.db_models import AppLog
from logic.page_list import pages
from logic.utils import database_to_excel_file_bytes

init_page(pages.restore_app_state)
st.set_page_config(layout='centered')


@st.dialog('ARE YOU SURE YOU WANT TO RESET ALL DATA TO THIS POINT?')
def restore_warning_dialog(snap: Snapshot):
    time_str = datetime_sentence(snap.time)
    msg = f"""The state of Dahu 2 will be reset to:\n\n**{time_str}**."""
    st.error(msg)
    if st.button('⚠️ **Confirm** ⚠️'):
        sess[Sk.SNAP_TO_RESTORE] = snap
        st.rerun()


@st.dialog('Please wait')
def restore_process_dialog(snap: Snapshot):
    del sess[Sk.SNAP_TO_RESTORE]
    with st.spinner("Restoring..."):  # noqa
        snap.restore()
    st.success(f"**Dahu 2 data was restored successfully.**")
    sleep(5)
    st.rerun()


def snapshot_row(snap: Snapshot):
    with st.container(border=True, horizontal=True,
                      horizontal_alignment='distribute',
                      vertical_alignment='center',
                      width=500):
        st.write(f'**{datetime_sentence(snap.time)}**')
        if st.button('Restore', key='restore'+snap.id):
            restore_warning_dialog(snap)


def body():
    if Sk.SNAP_TO_RESTORE in sess and sess[Sk.SNAP_TO_RESTORE]:
        snap = sess[Sk.SNAP_TO_RESTORE]
        restore_process_dialog(snap)

    st.header("Internal Logs")
    file_name = f'dahu_2_logs_{compact_datetime_str(datetime.now())}.csv'
    st.download_button('Download as CSV', data=AppLog.all_rows_to_csv(),
                       file_name=file_name)

    st.divider()

    st.header("Explore Database")

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
    restore points** (but no the selected restore point).
    
    **Restoration will affect data of all users.**
    """
    st.error(warning_msg, title="DANGER ZONE")

    st.write("Go back in time, restore app state (database and stored files) "
             "to a previous point in time. It will restore deleted data.")

    st.subheader("Available Restore Points")
    try:
        snapshots = Snapshot.list_available()
        if not snapshots:
            st.write('_No restore point created yet._')
        else:
            for snap in snapshots:
                snapshot_row(snap)
    except RuntimeError as e:
        st.error(f"**Unable to list available restore points. "
                 f"Error message:**\n\n{e}")
    next_time = app_metadata.next_backup_at
    st.subheader(f"Next backup: {datetime_sentence(next_time)}.")

body()
