from datetime import datetime
from time import sleep

import streamlit as st

from logic.constants import DB_PATH
from logic.lab_modelization.base_classes import db
from logic.page_list import pages

# Don't import anything from this file, as it will load it again and re-run
# the current page.


if not DB_PATH.exists():
    raise RuntimeError(f'Database connection failed. please check presence of '
                       f'file \"{DB_PATH}\" in Dahu 2 code base.')

tables = db.get_tables()
if not tables:
    raise RuntimeError(f'Database (location: {DB_PATH}) empty.')

page = st.navigation(list(pages))

try:
    print(f"Page run at {datetime.now()}")
    page.run()
except Exception as e:
    st.error("ERROR:")
    st.error(e)