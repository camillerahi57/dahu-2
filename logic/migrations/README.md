# `logic/migrations/`: scripts that create or change the database tables

This folder holds one-off scripts that are run by hand from a terminal,
never by the app. A **migration** is a script that changes the structure
of the database (its "schema": tables and columns) and moves the existing
data into the new structure. The scripts use the data model of
`logic/lab_modelization/` and the settings of `dahu_2_config.py`.

Run every script from the repo root, as a module, so that the project
imports work: `python -m logic.migrations.<script name without .py>`.

## Files

- **`table_creation.py`**: creates an empty database for a fresh install.
  It creates the SQLite file at `DB_PATH`, then one table per model in
  `dahu_2_models`.
  **DANGER: it also deletes every snapshot in the Restic repository set in
  `dahu_2_config.py` (`Snapshot.delete_all_snaps`). This cannot be undone.
  Never run it on an existing installation, and never in a dev setup that
  points at the production Restic repository.**

## Common tasks

### Write a migration after changing a model

SQLite cannot change a column in place, so the table is rebuilt.

1. Change the model in `logic/lab_modelization/db_models.py` (see
   `logic/lab_modelization/README.md`).
2. Create a new script in this folder. The main `README.md` names them
   after the date and the change, e.g. `2026_09_split_argon_flow.py`.
3. Write it with raw SQL (`db.execute_sql(...)`, with `db` imported from
   `logic.lab_modelization.base_classes`), not with Peewee objects and
   `save()`: many models write an `AppLog` row on every save, which needs
   a running Streamlit page. Table names are the model names in snake_case
   (`TriodeSputtering` → `triode_sputtering`). The steps are:
   1. `PRAGMA foreign_keys=OFF` (a pragma is a SQLite setting). Run it
      before opening the transaction: SQLite ignores it inside one.
   2. Inside `with db.atomic():` (a transaction: if one step fails,
      none of them is kept):
      1. `CREATE TABLE <table>_new (...)` with the new columns.
      2. `INSERT INTO <table>_new (...) SELECT ... FROM <table>` to copy
         and convert the rows.
      3. `DROP TABLE <table>`.
      4. `ALTER TABLE <table>_new RENAME TO <table>`.
   3. `PRAGMA foreign_keys=ON`.
4. Test it on a dev copy of `user_data/dahu_2.db` (never on the production
   file), check the data with DataGrip (read only), then click through
   every page that shows this table.
5. On production, after `git pull`, run the script **exactly once**, then
   restart Streamlit.

### Rename or delete an enum value

1. Write a migration script that runs an
   `UPDATE <table> SET <column> = 'new' WHERE <column> = 'old'` for every
   column annotated with that enum.
2. Change the value in `logic/lab_modelization/db_enums.py` in the same
   commit.
