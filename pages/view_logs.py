"""Logs page: lists the `AppLog` rows, newest first, with filters and
pagination (`LOG_PAGE_LENGTH` rows per page).

Warnings and critical errors can be marked read; critical errors can
also be marked solved. Until then they are coloured (orange or red) and
counted in the banner of the home page. The whole table can be
downloaded as CSV.

The index of the page of logs shown is kept in the session state
(Streamlit's per-tab dictionary that survives reruns) under
`Sk.LOG_PAGE`, counted from 0.
"""
from datetime import datetime

import streamlit as st

from components.general import init_page, compact_datetime_str, icon, \
    colored
from logic.constants import SessionKeys as Sk, LOG_PAGE_LENGTH
from logic.global_variables import sess
from logic.lab_modelization.db_enums import LogSeverity
from logic.lab_modelization.db_models import AppLog
from logic.page_list import pages

init_page(pages.view_logs)
st.set_page_config(layout='wide')

# After `init_page`, which deletes `Sk.LOG_PAGE` when the user comes
# from another page: the list then starts again at the first page.
if Sk.LOG_PAGE not in sess:
    sess[Sk.LOG_PAGE] = 0


def body():
    """Draw the page: CSV download, filters, page selector and logs."""
    st.header("Internal Logs")

    file_name = f'dahu_2_logs_{compact_datetime_str(datetime.now())}.csv'
    st.download_button('Download all as CSV', data=AppLog.all_rows_to_csv(),
                       file_name=file_name, icon=':material/download:')

    st.divider()

    filters = FilterSelector()

    log_query = AppLog.filtered_query(severities=filters.checked_severities,
            show_read=filters.marked_read, show_solved=filters.marked_solved)

    log_count = log_query.count()  # noqa Wrong warning.

    page_selector(log_count)

    st.divider(width=50)

    page_nb = sess[Sk.LOG_PAGE]
    # Peewee pages start at 1...:
    paginated_logs = log_query.paginate(page_nb+1, LOG_PAGE_LENGTH)
    for log in paginated_logs:
        log_row(log)


def page_selector(log_count: int):
    """Draw the first / previous / next / last buttons and the page number.

    Each button changes `Sk.LOG_PAGE` in the session state and reruns
    the page so that the new page of logs is drawn.

    Args:
        log_count: Number of logs that pass the filters.
    """
    # TODO With 0 logs, `page_count` is 0 and
    #   `last_page_idx` is -1, so the "next" and "last" buttons stay enabled
    #   and lead to page indexes -1 or 1. Also, `is_last_page` (line 75) uses
    #   `==`: after a filter reduces the number of pages, the current page can
    #   be beyond the last one, showing an empty list with "next" enabled.
    # Ceiling division: a partial last page counts as a page.
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
    """Draw one log on one line, with its buttons.

    Buttons: "Mark solved" (critical errors only), "Mark as read"
    (warnings and critical errors), and "..." which opens the details
    dialog. The text is orange for an unread warning, red for an
    unsolved critical error, grey otherwise. The description is cut to
    100 characters, with its line breaks replaced by " · ".

    Side effect: the mark buttons save the row (no new `AppLog` row: the
    `AppLog` model does not log its own saves).

    Args:
        log: The log to show.
    """
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
    """The row of filter checkboxes above the logs, and their values.

    Unchecking "Read" (or "Solved") hides the logs marked read (or
    solved); all logs are shown when every box is checked.

    Attributes:
        checked_severities: Severities to show. Every severity when no
            severity box is checked.
        marked_read: Whether to show logs marked read.
        marked_solved: Whether to show logs marked solved.
    """
    def __init__(self):
        """Draw the checkboxes (all checked at first) and read them."""
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
    """Show every column of a log in a pop-up window (a dialog).

    `st.write` displays the row's `__str__` (see `_BaseModel.__str__`):
    one "- column: value" line per column, so the full description.

    Args:
        log: The log to show.
    """
    st.write(log)

body()