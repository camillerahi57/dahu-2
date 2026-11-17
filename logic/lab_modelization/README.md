# `logic/lab_modelization/`: the data model

This folder describes what the database holds: one Python class per table,
the fixed lists of allowed values, and the base class with the shared
saving, deleting and checking logic. Almost every other part of the app
imports it: the other `logic/` modules, the pages in `pages/` and the forms
in `pages/components/forms/`. It uses `logic/constants.py`,
`logic/units.py`, `logic/math_tools.py`, `logic/page_list.py` and
`dahu_2_config.py`.

A few words used below:

- **ORM** (object-relational mapper): a library that lets us handle database
  rows as Python objects. Ours is Peewee. A **model** is a class whose
  instances are rows of one table; its class attributes are the columns.
- **Foreign key**: a column holding the id of a row of another table. The
  rows pointing back to a given row are its **backref**.
- **Parts**: the rows that belong to an object and are saved and deleted
  with it (the layers of a substrate, the patches of a target state...).
  They are the attributes annotated `DependentBackref[...]`.
- **Subtype**: a separate table holding the details of one kind of general
  row (e.g. `Annealing` for a `FilmModification`), linked by a unique
  foreign key. An enum column on the general row says which subtype applies.
- **Transaction** (`with db.atomic():`): a group of writes that either all
  succeed or are all cancelled.

## Files

- **`base_classes.py`**: what every table shares. Open it to understand how
  saving a whole form result or deleting an object with its parts works.
  - `db`: the one Peewee database object (SQLite file `user_data/dahu_2.db`,
    with foreign keys enforced).
  - `_BaseModel`: parent of every table. `save_with_dependent()` saves an
    object and its parts recursively; `delete_with_parts()` deletes them;
    `data_string()` shows values in UI units; `get_problems()` is the
    integrity check; `save()` and `delete_instance()` write an `AppLog` row
    when `log_db_write` is True.
  - `DependentBackref[T]`: annotation marking an attribute as a list of
    parts.
  - `Event`: something to log (a save, a missing file, a Restic error...),
    stored as an `AppLog` row by `AppLog.save_new`.

- **`db_models.py`**: every table of the database, grouped by topic in the
  module docstring (substrates, targets, libraries and films, film
  modifications, characterizations, uploaded files, app bookkeeping). Open
  it to find what a column means, its SI unit and whether it can be NULL:
  each class docstring lists its columns under `Attributes:`.
  - `Library`, `Film`, `FilmLayer`, `Target`, `Substrate`: the main lab
    objects.
  - `UserUploadedFile`: parent of every uploaded file (`Pattern`, `Recipe`,
    `LibraryFile`, `CharacFile`, `TargetPhoto`). The row holds the
    metadata, the bytes are in `user_data/<internal_file_name>`.
  - `AppMetadata`: a **singleton** table (it only ever holds one row) with
    the backup and problem-check schedule and the app version.
  - `AppLog`: the event log shown on the logs page and the home page banner.
  - `dahu_2_models`: the list of all models, collected automatically from
    this file. Table creation, the integrity checks and the Excel export use
    it.

- **`db_enums.py`**: the allowed values of the text columns that take one
  value from a fixed list, as `StrEnum`s (an enum whose members compare
  equal to plain strings). The string is what the database stores. Open it
  to add a choice to a select box. Key enums: `SputteringSystem` and
  `FilmModifType` (which subtype table applies), `CharacType`,
  `ChemicalElement`, `EventType` and `LogSeverity` (for `AppLog`). Some
  enums are only suggestions offered in forms (`Etching...Suggestion`),
  and some are not used yet (their docstrings say so).

- **`other_classes.py`**: plain Python classes of the data model that are
  not tables. Only `MixtureConstituent` (one gas of an ion beam etching
  plasma, as used by the etching form).

**Warnings**

- **Never rename or delete an enum value in `db_enums.py`** without a
  migration that updates the stored rows: rows holding the old string no
  longer match any member. Adding values is always safe. Renaming the
  Python name (`POLYGON` → `POLY`) is safe too, since only the string is
  stored.
- **Any change to a column or table needs a migration script**, run once on
  production (see `logic/migrations/README.md`). Changing `db_models.py`
  alone makes the code disagree with the existing database file.
- **New tables must be defined in `db_models.py`**, otherwise
  `dahu_2_models` misses them: they would not be created, checked or
  exported.
- Saving or deleting rows of a model with `log_db_write = True` writes an
  `AppLog` row, which reads the browser cookies and so needs a running
  Streamlit page. Scripts run outside the app must use raw SQL instead.
- The EDX models (`Edx`, `ChemicalElementEdx`) belong to a feature that is
  still in development.

## Common tasks

### Add a column to an existing table

1. Check that it is worth it: the main `README.md` ("Attribute choices")
   only allows a new attribute if it must be searchable, is accessed
   frequently, or is not stored in uploaded files AND can change AND
   affects measurements.
2. In `db_models.py`, add the Peewee field to the class, add a keyword of
   the same name to its `__init__`, and describe the column (meaning, SI
   unit, NULL or not) under `Attributes:` in the class docstring. Store
   physical quantities in SI base units.
3. If the column takes values from a fixed list, add a `StrEnum` to
   `db_enums.py` and annotate the column with it
   (`x: MyEnum = cast(Any, CharField())`). Write `MyEnum | None` for a
   nullable column; the integrity check then skips it.
4. To show it on the inspection pages, add a `(title, value, FieldClass)`
   tuple to the model's `title_db_value_input_fields`.
5. Add the form field in `pages/components/forms/new_<thing>/fields.py`,
   use it in `sub_forms.py`, and pass its value in the `to_<model>()`
   method of the `RootForm`.
6. Write the migration script in `logic/migrations/` and test it on a dev
   copy of the database.

### Add a new table

1. In `db_models.py`, write a class that subclasses `_BaseModel`, with:
   its columns, a keyword `__init__` that calls
   `self.get_model_kwargs(locals())`, and a `delete_parts()` method (just
   `pass` if it has no parts). Set `log_db_write = True` if its changes
   should appear in the logs.
2. If it is a part of another model, give it a foreign key with
   `on_delete='RESTRICT'` (or `'CASCADE'`) and a `backref` name. Annotate
   that name on the parent with `DependentBackref[NewModel]`, and delete
   the new rows in the parent's `delete_parts()`.
3. Write a migration script in `logic/migrations/` that creates the table
   on the existing database.

### Add a value to a select box backed by an enum

1. Add a member to the right enum in `db_enums.py`. Nothing else is
   needed.
