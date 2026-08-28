from datetime import datetime

import streamlit as st

from components.general import init_page, compact_datetime_str, sess, icon, \
    colored
from logic.constants import SessionKeys as Sk, LOG_PAGE_LENGTH
from logic.lab_modelization.db_enums import LogSeverity
from logic.lab_modelization.db_models import AppLog
from logic.page_list import pages

init_page(pages.view_logs)
st.set_page_config(layout='wide')

if Sk.LOG_PAGE not in sess:
    sess[Sk.LOG_PAGE] = 0


def body():
    st.header("Internal Logs")

    file_name = f'dahu_2_logs_{compact_datetime_str(datetime.now())}.csv'
    st.download_button('Download all as CSV', data=AppLog.all_rows_to_csv(),
                       file_name=file_name, icon=':material/download:')

    st.divider()

    filters = FilterSelector()

    log_query = AppLog.filtered_query(severities=filters.checked_severities,
            show_read=filters.marked_read, show_solved=filters.marked_solved)

    log_count = log_query.count()  # noqa Wring warning.

    page_selector(log_count)

    st.divider(width=50)

    page_nb = sess[Sk.LOG_PAGE]
    # Peewee pages start at 1...:
    paginated_logs = log_query.paginate(page_nb+1, LOG_PAGE_LENGTH)
    for log in paginated_logs:
        log_row(log)


def page_selector(log_count: int):
    page_count = (log_count - 1) // LOG_PAGE_LENGTH + 1
    last_page_idx = page_count - 1
    is_first_page = sess[Sk.LOG_PAGE] == 0
    is_last_page = sess[Sk.LOG_PAGE] == last_page_idx

    with st.container(horizontal=True, vertical_alignment='center'):
        if st.button('', disabled=is_first_page, icon=icon('first_page')):
            sess[Sk.LOG_PAGE] = 0
            st.rerun()

        if st.button('', disabled=is_first_page, icon=icon('arrow_back')):
            sess[Sk.LOG_PAGE] -= 1
            st.rerun()

        st.write(f"Page {sess[Sk.LOG_PAGE]+1}")

        if st.button('', disabled=is_last_page, icon=icon('arrow_forward')):
            sess[Sk.LOG_PAGE] += 1
            st.rerun()

        if st.button('', disabled=is_last_page, icon=icon('last_page')):
            sess[Sk.LOG_PAGE] = last_page_idx
            st.rerun()


def log_row(log: AppLog):
    with (st.container(horizontal=True, vertical_alignment='center',
                      height='content')):
        is_critical = log.severity == LogSeverity.CRITICAL
        if is_critical:
            solved = log.marked_solved
            bttn_label = f'Mark unsolved' if solved else f'Mark solved'
            if st.button(bttn_label, key=f'solved_{log.id}'):
                log.marked_solved = not log.marked_solved
                log.save()
                st.rerun()

        is_problem = log.severity in {LogSeverity.WARNING, LogSeverity.CRITICAL}
        if is_problem:
            if log.marked_read:
                bttn_label = f'Mark as unread'
            else:
                bttn_label = f'Mark as read'
            if st.button(bttn_label, key=f'read_{log.id}'):
                log.marked_read = not log.marked_read
                log.save()
                st.rerun()

        if log.severity == LogSeverity.WARNING and not log.marked_read:
            text_color = 'orange'
        elif log.severity == LogSeverity.CRITICAL and not log.marked_solved:
            text_color = 'red'
        else:
            text_color = 'gray'

        columns = [
            f"**{LogSeverity(log.severity).icon} "
                f"{colored(log.severity.capitalize(), text_color)}**",
            log.timestamp.strftime('%Y-%m-%d   %H:%M:%S'),
            f'**{log.event_type}:**',
            f"*{log.event_description.replace('\n', ' · ')[:100]}*"
        ]
        for c in columns:
            st.write(colored(c, text_color))
        if st.button('', icon=icon('more_horiz'), key=f'details_{log.id}'):
            log_dialog(log)


class FilterSelector:
    def __init__(self):
        with st.container(horizontal=True, vertical_alignment='center'):
            st.write('**Show:** ')
            severity_boxes = {
                severity: st.checkbox(severity.capitalize(), value=True)
                for severity in LogSeverity
            }
            st.write(' | ')
            marked_read_box = st.checkbox('Read', value=True)
            marked_solved_box = st.checkbox('Solved', value=True)

        checked_severities = [severity
                              for severity, checked in severity_boxes.items()
                              if checked]
        if not checked_severities:
            # Nothing checked becomes equivalent to everything checked:
            checked_severities = list(LogSeverity)

        self.checked_severities = checked_severities
        self.marked_read = bool(marked_read_box)
        self.marked_solved = bool(marked_solved_box)


@st.dialog('Log details', width='large')
def log_dialog(log: AppLog):
    st.write(log)

body()