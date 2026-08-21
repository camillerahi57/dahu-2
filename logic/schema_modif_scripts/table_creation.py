import sqlite3

from logic.app_restoration import Snapshot
from logic.lab_modelization.db_models import all_models, db

"""Don't call create_tables for abstract models (parent models that will 
never have an instance, like Shape for example). Peewee don't use parent 
class for storing common attributes. It copies all attributes in child 
classes."""

# Create the DB file:
with sqlite3.connect('user_data/dahu_2.db') as connection:
    pass

# Delete backups:
Snapshot.delete_all_snaps()
# Create the tables in the DB:
db.create_tables(all_models())