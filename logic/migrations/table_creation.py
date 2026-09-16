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