# `pages/components/forms/new_library/`: forms of the library and film pages

The form of the "new library" page (`pages/new_lib.py`): the library, its
film, the targets used and the film's layers with their sputtering
parameters. Parts of it are reused by the edit pages: `BaseInfoForm` by
`pages/edit_lib.py`, `FilmInfoForm` by `pages/edit_film.py`, and
`TargetListForm` with `LayerListForm` by `../edit_film_layers/`. It builds
on `../base_classes.py`.

Some field classes are also used outside forms, only for their unit: the
models' `title_db_value_input_fields` in
`logic/lab_modelization/db_models.py`, `logic/table_columns.py` and
`pages/inspect_library.py` call their `db_to_ui_str()` to show stored
values. **Changing a `ui_unit` here also changes how existing values are
displayed in tables and on the library page** (the stored values, in SI
base units, are unaffected).

## Files

- **`fields.py`**: one class per input (about 40), roughly in the order
  of the form. Open it to change a label, a UI unit, a default or a
  validation rule. Examples: `LibLabelField` (unique library label),
  `TargetChoiceField` (the target of one layer, chosen among the targets
  listed above it), `SputteringSystemField` (magnetron or triode),
  `DepositTempField` and `NominalThicknessField` (unit fields: typed in
  °C and nm, stored in K and m), `ConfirmOrderField` (the "layer order is
  right" checkbox). Each docstring gives the UI and DB units.
- **`sub_forms.py`**: the forms, nested as follows (the module docstring
  has the full tree):
  - `RootForm`: the whole page. Its `library` attribute is the unsaved
    `Library` with its film, layers and their parts (the rows each object
    owns), which the page saves with `save_with_dependent()`.
  - `BaseInfoForm` (library label, comment) and `FilmInfoForm` (film
    label, date, author, substrate).
  - `TargetListForm`: the targets used for the film. They are not saved
    as such; they fill the target choices of each layer.
  - `LayerListForm` → one `LayerForm` per layer, bottom first →
    `LayerIntroForm` (general data, targets, sputtering system), then
    `MagnetronForm` or `TriodeForm`. `LayerForm.to_layer` builds the
    unsaved `FilmLayer` with its parts.

**`TargetListForm` must be drawn before `LayerListForm`.** It writes the
chosen target labels to the session state (`SessionKeys.SELECTED_TARGETS`;
the session state is a dictionary Streamlit keeps for each browser tab
across reruns), and the layer forms read them from there.

**The nitrogen flow of triode layers is stored as typed**:
`NitrogenFlowField` is labelled in SCCM..

Many builder methods (`to_library`, `add_to_layer`...) raise
`PausePageRun` while their form is invalid. Every widget is already drawn
by then, so this only hides what comes next, such as the Submit button.

## Common tasks

### Add a parameter to a magnetron (or triode) layer

1. Add the column to `MagnetronSputtering` (or `TriodeSputtering`) in
   `logic/lab_modelization/db_models.py`, and write its migration (see
   `logic/lab_modelization/README.md`).
2. In `fields.py`, add a field class. For a physical quantity, subclass
   `UnitField` and set `ui_unit` (e.g. `ui_unit = ur.mm`); the database
   gets SI base units automatically. Copy `DepositDistanceField`.
3. In `sub_forms.py`, in `MagnetronForm.__init__` (or `TriodeForm`):
   create the field with `key=key` and `db_default=` the existing value
   (so the edit film layers page is prefilled), store its value
   (`.in_db_unit` for a unit field, `.value` otherwise), and add it to the
   `fields=[...]` list of `super().__init__`.
4. Pass the value to `MagnetronSputtering(...)` in `add_to_layer`.
5. To show it in the layer details on the library page, add a
   `(title, value, FieldClass)` tuple to the model's
   `title_db_value_input_fields`.

### Add a parameter common to every layer

1. Same steps, with the column on `FilmLayer`, the field drawn in
   `LayerIntroForm.__init__` and the value passed in `LayerForm.to_layer`.
