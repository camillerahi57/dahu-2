# `logic/`: everything that is not drawing the web page

This folder holds the data model, unit conversions, backups and restores,
integrity checks, the list of pages and the shared constants. The pages
(`pages/*.py`) and the shared UI code (`pages/components/`) import it;
`logic/` reads its settings from `dahu_2_config.py`. Two places import
back from `pages/components/`: `table_columns.py`, and
`_BaseModel.data_string` (inside the method, to avoid a circular import,
i.e. two modules that each need the other to be loaded first).

**Importing some of these modules does real work.** Python runs the
top-level code of a module the first time it is imported, and some
modules here read the database, need a running Streamlit page or raise an
error (see each entry). So don't import them from a plain script unless
you know what they do.

## Subfolders

- **`lab_modelization/`**: the data model: one Peewee class per database
  table (`db_models.py`), the allowed values of the text columns
  (`db_enums.py`) and the shared base class (`base_classes.py`). Open it
  for anything about what is stored. See its `README.md`.
- **`migrations/`**: scripts run by hand to create the database or change
  its tables. **`table_creation.py` deletes every Restic snapshot.** See its
  `README.md`.

## Files

- **`app_restoration.py`**: backups and restores through Restic, the
  backup program, run as a separate process. A snapshot is a copy of the
  whole `user_data/` folder (database and uploaded files together).
  `Snapshot.backup` is started by `init_page` in a background thread (a
  task running in parallel with the page) when a backup is due;
  `Snapshot.restore` and `Snapshot.list_available` are used by the admin
  page; `delete_excessive_snapshots` applies the `BackupsToKeep` policy.
  **`Snapshot.restore` replaces the whole `user_data/` folder and deletes
  every later snapshot. `Snapshot.delete_all_snaps` deletes them all.**
- **`constants.py`**: names and fixed values shared by the whole app.
  `IdType` (names of the query parameters, the `?lib_id=3` part of a URL
  that tells a page which object to show), `SessionKeys` (keys of
  `st.session_state`, Streamlit's per-tab memory that survives reruns),
  `CookieKeys` (keys of the cookies, small texts the browser keeps between
  visits), and `DB_PATH` / `USER_DATA_PATH`. **Never change the string
  values of `CookieKeys`**: browsers would lose their saved filters and
  email. The paths are relative, so the app must be started from the repo
  root.
- **`cookie_init.py`**: creates `cookies`, the object that reads and
  writes the browser's cookies. Import `cookies` from here. On import it
  needs a running Streamlit page, may wait about 5 s and may write
  `AppLog` rows.
- **`db_integrity.py`**: `get_problems()`, the periodic check run by
  `init_page`: each model's `get_problems()` (unknown enum values, missing
  uploaded files), then the age of the last Restic snapshot. Open it to
  add a check that is not about one table.
- **`global_variables.py`**: `sess` (short name for `st.session_state`)
  and `ON_PRODUCTION`. **On import it raises an error unless the
  environment variable `dahu_db_production_mode` is `True` or `False`.**
  `dahu_2_config.py` imports it to choose between its production and
  development settings.
- **`math_tools.py`**: small geometry helpers for the patches drawn on
  target photos, in pixel coordinates: `Point`, `VertexList`, `Disc`
  (`from_circumference_points`, `to_vertices`), `get_constrained_size`
  for fitting an image in a box, and `to_float` for Pint quantities.
- **`meta_data_init.py`**: loads `app_metadata`, the single `AppMetadata`
  row (backup and problem-check schedule), once per server process. Reads
  the database on import.
- **`page_list.py`**: `pages`, the list of every page of the app; use
  `pages.<name>` wherever a page is needed. `entry_point.py` gives it to
  `st.navigation`. `from_url_path` finds a page by its URL. **Changing a
  `url_path` breaks saved links and bookmarks.**
- **`table_columns.py`**: column titles of the tables on the browsing
  pages and the library page (`LibraryBrowserColumnName`,
  `TargetBrowserColumnName`, `SubstrateBrowserColumnName`,
  `LibInspectColumnName`). Titles with a unit take it from the form
  field's `ui_unit`, which is why this file imports from
  `pages/components/forms/`.
- **`units.py`**: conversions between UI units and the SI base units
  stored in the database, with Pint (the library that attaches units to
  numbers). `ur` is the unit registry to use everywhere;
  `to_db_magnitude` and `from_db_unit` convert; `db_units` gives the DB
  unit of each kind of quantity. Most code does not call it directly: the
  form field classes (`UnitField`) do.
- **`utils.py`**: small helpers. `reset_session` (clears the app's
  session-state keys), `is_valid_email_address` (also saves the address in
  a cookie), `rand_str`, `database_to_excel_file_bytes` (the admin page's
  Excel export), and `all_email_addresses` (choices of the email fields,
  read from the database on import, so new addresses only appear after a
  restart).

## Common tasks

### Add a page

1. Create `pages/<name>.py`. Start it with `init_page(pages.<name>)` and
   wrap its body in `try: ... except PausePageRun: pass`.
2. Register it in `page_list.py`: add an attribute to `_Pages` with a
   `Page('../pages/<name>.py', url_path=..., title=..., icon=...)`.
3. Link to it with `switch_page_bttn(pages.<name>, ...)`. Never import
   the page file from another module: Streamlit runs pages as scripts, so
   the import would run it a second time. Put shared code in
   `pages/components/`.

### Let a page receive a new kind of object in its URL

1. Add a member to `IdType` in `constants.py` (e.g. `PATTERN =
   'pattern_id'`).
2. Read it in the page with `current_params()[IdType.PATTERN]`, and add
   it to the links that open the page.

### Remember a new per-browser choice in a cookie

1. Add a member to `CookieKeys` in `constants.py`, with a new random
   string as value (never reuse or change an existing one).
2. Read and write it with `cookies.get(...)` and `cookies.set(...)`,
   importing `cookies` from `cookie_init.py`.

### Add a check to the periodic problem scan

1. For a check about one table, override `get_problems` on the model in
   `lab_modelization/db_models.py` (see `UserUploadedFile.get_problems`).
   For another kind of check, add it to `get_problems` in
   `db_integrity.py`.
2. Add an `EventType` value in `lab_modelization/db_enums.py` and an
   `Event.from_...` constructor in `lab_modelization/base_classes.py`
   describing the problem.

### Change how often backups run or how many are kept

1. Edit `BACKUP_INTERVAL` and `BackupsToKeep` in `dahu_2_config.py`.
   Nothing in `logic/` needs to change.
