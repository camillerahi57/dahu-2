"""Creates an empty Dahu DB database. For fresh installs only.

Run once, from the repo root:
`python -m logic.migrations.table_creation`.

WARNING: it also deletes every snapshot in the Restic repository set in
`dahu_2_config.py`. Never run it on an existing installation.

What it does, in order:
    1. Creates the SQLite file at `DB_PATH` if it doesn't exist.
    2. Deletes all Restic snapshots.
    3. Creates one table per model in `dahu_2_models` (Peewee skips
       tables that already exist).
"""
import sqlite3

from logic.app_restoration import Snapshot
from logic.constants import DB_PATH
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import dahu_2_models

"""Don't call create_tables for abstract models (parent models that will 
never have an instance, like Shape for example). Peewee don't use parent 
class for storing common attributes. It copies all attributes in child 
classes."""

# Create the DB file:
connexion = sqlite3.connect(DB_PATH)

# Delete backups:
Snapshot.delete_all_snaps()
# Create the tables in the DB:
db.create_tables(dahu_2_models)

