# `pages/components/forms/`: the input forms of the app

Everything the user fills in (new and edit pages) is built from the
classes in `base_classes.py`, assembled in one package (subfolder) per
kind of object. The pages in `pages/` import a package's `RootForm`, draw
it, and save the object it builds. The forms use the data model
(`logic/lab_modelization/`) and the unit conversions (`logic/units.py`).
In the other direction, some models and `logic/table_columns.py` import
field classes from here, only to display stored values in the right unit.

## How fields and forms work

A few words used below:

- **Rerun**: Streamlit runs the whole page script again, from the top,
  every time the user changes a widget. Forms are therefore rebuilt from
  scratch on every click.
- **Widget key**: the name Streamlit uses to recognize a widget from one
  rerun to the next. Two widgets with the same key on one page make
  Streamlit raise an error.
- **Session state** (`st.session_state`, often `sess`): a dictionary
  Streamlit keeps for each browser tab, the way values survive reruns.
- **Abstract base class**: a class meant only to be subclassed. Its
  *abstract methods* must be written by every subclass.
- **Object graph**: an unsaved object with its *parts* (the child rows
  it owns, such as the layers of a substrate) attached as lists. The page
  saves it all at once with `save_with_dependent()`.

How it fits together:

1. A **field** (`Field` subclass) is one widget. Creating it draws the
   widget, reads the input, validates it and shows a warning if it is
   invalid; so create it where it should appear on the page. Each
   subclass writes `_streamlit_input` (draws the widget), `_validate`
   (returns `(ok, message)`) and sets `type` (`MANDATORY`, `ADVISED` or
   `OPTIONAL`; an empty mandatory field is invalid).
2. A **unit field** (`UnitField` subclass) is a field for a physical
   quantity. It declares `ui_unit` once; read its input with
   `.in_db_unit` (SI base units, what the database stores). `.value`
   raises an error on purpose.
3. A **form** (`Form` subclass) creates its fields and sub-forms in its
   `__init__`, stores their values, then calls
   `super().__init__(fields, sub_forms)`, which sets `is_valid`. Rules
   involving several fields go in `_is_coherent`.
4. Each package ends with a `RootForm` that builds the unsaved object
   graph. The page shows a Submit button disabled while
   `root_form.is_valid` is False, then saves inside `with db.atomic():`
   (a transaction: the writes all succeed or are all cancelled).

Defaults: `form_default` prefills a "new" page; `db_default`, the value
from an existing object, overrides it on edit pages.

**Always call `super().__init__(fields, sub_forms)` at the end of a
form's `__init__`, listing every field and sub-form.** If you forget it,
or leave something out of the lists, its validity is silently ignored
and the Submit button may be enabled for an invalid form.

**Widget keys are `<class name>_<key>`.** When the same field class
appears twice on a page (one per layer, one per patch...), give each a
distinct `key`, usually the index. Some fields ignore `key` (their
docstring says so) and can only appear once per page.

## Files

- **`base_classes.py`**: the building blocks. Open it to understand how
  any form works.
  - `Field`, `FieldType`, `UnitField`: fields, as described above.
  - `Form`: a group of fields and sub-forms, valid as a whole.
  - `FileUploadForm` (with `FileUploadField` and `FileLabelField`): pick
    a file and give it a label; keeps the file in the session state across
    reruns. Used by the upload pages (patterns, recipes, library files).
  - `PausePageRun`: an exception raised to stop drawing the rest of the
    page, e.g. while a step is unfinished. Every page catches it.

## Subfolders

Each holds `fields.py` (one class per input) and/or `sub_forms.py` (the
forms, ending with `RootForm`), and has its own `README.md`.

- **`new_library/`**: library, film, targets used and film layers
  (magnetron or triode sputtering). Also used by the edit library, edit
  film and edit film layers pages.
- **`new_substrate/`**: substrate and its layers; also used by the edit
  substrate page. The smallest package: a good example to copy.
- **`new_target/`**: target and its first deterioration state (photo,
  scale, patches). Its state form is reused by the two deterioration
  state packages, its basic info form by the edit target page.
- **`new_deterioration_state/`**: a new state of an existing target.
- **`edit_deterioration_state/`**: change an existing state.
- **`edit_film_layers/`**: change the targets and layers of a film.
- **`new_film_modif/`**: an annealing or etching of a film, with one
  subfolder per kind.
- **`new_charac/`**: empty; presumably for a future "new
  characterization" form.

## Common tasks

### Add an input to an existing form

1. Add the database column first if needed (see
   `logic/lab_modelization/README.md`, "Add a column to an existing
   table").
2. Add a field class to the package's `fields.py`: subclass `Field` (or
   `UnitField` with a `ui_unit` for a physical quantity), set `type`, and
   write `_streamlit_input` and `_validate`. Pass `key` to the widget.
3. In `sub_forms.py`, create the field in the right form's `__init__`
   with `form_default` and `db_default`, store its value, and add it to
   the `fields` list of `super().__init__`.
4. Pass the value to the model in that form's builder method
   (`to_<model>`, `add_to_<parent>`...).

### Add a check involving several fields

1. Write it in the form's `_is_coherent`, which returns
   `(True, '')` or `(False, '<message shown to the user>')`.

### Change the unit an input is typed in

1. Change `ui_unit` on the field class. Conversions and labels follow,
   and stored values stay in SI base units. Existing values are then also
   displayed in the new unit wherever that class is used for display.
2. If the class also sets `ui_unit_alias` (a text its label shows
   instead of the unit, e.g. `'SCCM'`), update that text too.
