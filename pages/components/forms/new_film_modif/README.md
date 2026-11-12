# `pages/components/forms/new_film_modif/`: form of the film modification page

The form of `pages/new_film_modif.py`, which records a modification of a
film: an annealing or an etching (ion beam, wet, or lift-off). The
information common to every modification is asked here; the rest comes
from the sub-package of the chosen kind. It builds on
`../base_classes.py`.

The database stores a modification as a general `FilmModification` row
plus a *subtype*: a separate table holding the details of one kind of
modification (`Annealing`, or `Etching` and then `IonBeamEtching`,
`WetEtching` or `LiftOffEtching`). The `modif_type` column says which
subtype applies. The form mirrors this: one general form, then one
sub-form per subtype.

## Subfolders

Each holds a single `sub_forms.py` and has its own `README.md`.

- **`annealing/`**: `AnnealingForm`, the furnace settings and the list of
  temperature phases (ramps and plateaus), turned into `AnnealingStep`s.
- **`ion_beam_etching/`**: `IonEtchingForm`, the machine settings and the
  plasma gas mixture.
- **`wet_etching/`**: `WetEtchingForm`, development, bake, acid, solvents
  and etching speeds.
- **`lift_off/`**: `LiftOffForm`, the ultrasound settings.

## Files

- **`sub_forms.py`**: the top-level forms. Open it to see how a
  modification is put together.
  - `RootForm`: draws `ModifBaseInfoForm`, then, depending on the chosen
    type, the form of one subfolder (a `match` on `FilmModifType`). Its
    `film_modif` attribute is the unsaved `FilmModification` with its
    subtype rows, which the page saves with `save_with_dependent()`.
  - `ModifBaseInfoForm`: type, date, author, position in the film's
    history and comment; `to_film_modif` builds the `FilmModification`
    row. Its `_is_coherent` refuses a date earlier than the previous
    modification's.
- **`shared.py`**: sub-forms used by several etching forms.
  - `EtchingForm` (with `PatternForm`): the recipe and pattern, chosen by
    label among the files uploaded on the browse recipes and browse
    patterns pages; `to_etching` builds the general `Etching` row. Used
    by all three etching forms.
  - `ConstituentListForm` (with `ConstituentForm`): a gas mixture, as
    formulas and relative proportions; `to_plasma` normalizes the
    proportions. Only the ion beam etching uses it.
- **`fields.py`**: every input of these forms (about 45), for all kinds
  of modification. Examples: `ModifTypeField` (which sub-form is drawn),
  `MadeAfterField` (where the modification goes in the film's history),
  `PhaseTypeField` and `ReachedTempField` (annealing phases),
  `FlowField` (typed in SCCM, stored in m³/s). Each docstring gives the UI
  and DB units.

**Some field classes are also used outside forms, for their unit**:
`title_db_value_input_fields` and `AnnealingStep.get_figure` in
`logic/lab_modelization/db_models.py` use them to display stored values.
Changing a `ui_unit` here also changes how existing values are displayed,
including the axes of the annealing temperature plot.

**Many fields don't pass `key` to their widget.** Streamlit then builds
the widget key (the name it uses to recognize a widget from one rerun to
the next) from the label, so such a field can appear only once per page.
Their docstrings say "`key` is not used".

**Saving a modification renumbers other modifications**: saving one with
`modif_number` n adds 1 to every existing modification numbered n or
more. As written, this affects the modifications of every film, not only
this one; the `TODO POSSIBLE BUG` comment in `FilmModification.save`
(`logic/lab_modelization/db_models.py`) describes the problem.

No page edits a film modification yet: the `default_...` arguments of the
forms are always None.

## Common tasks

### Add a field to one kind of modification

1. Follow "Common tasks" in the README of that kind's subfolder.

### Add a new kind of etching

1. Add a member to `FilmModifType` in
   `logic/lab_modelization/db_enums.py`. The type radio buttons
   (`ModifTypeField`) list every member automatically.
2. In `logic/lab_modelization/db_models.py`, add the subtype table with a
   unique foreign key to `Etching` (a column holding the id of the
   `Etching` row) and a `backref` name; annotate that name on `Etching`
   with `DependentBackref[...]` and delete its rows in
   `Etching.delete_parts`. Write the migration script.
3. Create a subfolder with a `sub_forms.py` and a `README.md`. Copy
   `lift_off/`: a form that draws `EtchingForm` from `shared.py`, and a
   `to_..._etching(film_modif)` method that raises `PausePageRun` while
   the form is invalid and attaches the subtype row to the `Etching`.
4. Add a `case` for the new type in `RootForm.__init__` in
   `sub_forms.py`, and list the new subfolder in this README.
5. Add a `case` in `film_modif_info` in `pages/inspect_library.py`, which
   raises an error for unknown types.
