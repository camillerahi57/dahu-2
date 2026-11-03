"""Loads the app's metadata row once, when this module is first imported.

`AppMetadata` is a singleton table: it holds a single row (a singleton is
something there is only one of), with app-wide settings such as when the
next Restic backup and the next problem check are due. Python runs a
module only on its first import, so every module that does
`from logic.meta_data_init import app_metadata` shares the same object.

Side effects: reads the DB on import. If the table is empty, the object
built is not saved yet (see `AppMetadata.get_or_new`).
"""
from logic.lab_modelization.db_models import AppMetadata

# The shared metadata object, read by `init_page` and updated after each
# backup or restore in `logic.app_restoration`.
app_metadata = AppMetadata.get_or_new()
