"""Main script of the app: the file given to `streamlit run`.

Streamlit re-executes this script from the top on every page load and
every rerun (a rerun is Streamlit re-executing the script after each
click or widget change). Each time, it checks that the database file
exists and has tables, then lets `st.navigation` pick the page matching
the URL (the first registered page, `browse_libs`, when the URL has no
page path) and runs that page's file.

In production, an exception raised by a page is shown as an error on
the web page instead of stopping the app; in dev it is raised again, so
the full traceback appears.

Raises:
    RuntimeError: If `user_data/dahu_2.db` is missing or has no table.
"""
from datetime import datetime

import streamlit as st

from logic.constants import DB_PATH
from logic.global_variables import ON_PRODUCTION
from logic.lab_modelization.base_classes import db
from logic.page_list import pages

# Don't import anything from this file, as it will load it again and re-run
# the current page.

# TODO Auto-run on Windows startup (in case there's a Windows update, which
#  is very frequent).
#  PowerShell: `python -m streamlit run pages/entry_point.py`.

if not DB_PATH.exists():
    raise RuntimeError(f'Database connection failed. please check presence of '
                       f'file \"{DB_PATH}\" in Dahu DB code base.')

# The file can exist without any table, e.g. on a fresh install before
# `logic/migrations/table_creation.py` was run.
tables = db.get_tables()
if not tables:
    raise RuntimeError(f'Database (location: {DB_PATH}) empty.')

page = st.navigation(list(pages))

try:
    print(f"Page run at {datetime.now()}")
    page.run()
# `st.rerun`, `st.stop` and `st.switch_page` work by raising exceptions
# that derive from `BaseException`, not `Exception`, so this does not
# catch them.
except Exception as e:
    if ON_PRODUCTION:
        st.error("ERROR")
        st.error(e)
    else:
        raise e