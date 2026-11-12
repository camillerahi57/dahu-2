# `pages/components/forms/new_film_modif/annealing/`: the annealing form

The part of the film modification form that describes an annealing. It is
drawn by `RootForm` in `../sub_forms.py` when the user picks "annealing" as
the modification type. It takes its fields from `../fields.py` and its base
classes (`Form`, `PausePageRun`) from `../../base_classes.py`.

The user describes an annealing as a list of *phases*: a ramp (the
temperature changes linearly up to a new value) or a plateau (it stays the
same). The database does not store phases but `AnnealingStep`s, the points
between phases, so `n` phases give `n + 1` steps.

## Files

- **`sub_forms.py`**: every form of the annealing, from the outside in.
  Open it to change what is asked about an annealing or how phases become
  steps.
  - `AnnealingForm`: the entry point; draws the two forms below and
    builds the unsaved `Annealing` row with its steps (`to_annealing`).
  - `AnnealingIntroForm`: furnace, start pressure (typed in mbar, stored
    in Pa) and pumping time (typed in min, stored in s).
  - `PhaseListForm`: the phase count, then one `PhaseForm` each. Its
    `_is_coherent` requires a ramp up first and a ramp to room temperature
    last; `to_steps` turns the phases into `AnnealingStep` rows.
  - `PhaseForm`: one phase in a bordered box (type, atmosphere or vacuum,
    then `RampPhaseForm` or `PlateauPhaseForm`).

Every class takes `default_...` arguments to prefill it from an existing
annealing, but no page passes one yet: there is no page to edit a film
modification.

## Common tasks

### Add a setting to the annealing (not to one phase)

1. Add the column to `Annealing` in `logic/lab_modelization/db_models.py`
   and write its migration (see `logic/lab_modelization/README.md`).
2. Add the field class to `../fields.py` (a `UnitField` subclass with a
   `ui_unit` for a physical quantity).
3. In `sub_forms.py`, draw it in `AnnealingIntroForm.__init__`, store its
   value (`.in_db_unit` for a unit field, `.value` otherwise), add it to
   the `fields=[...]` list of `super().__init__`, and pass it to the
   `Annealing(...)` call in `AnnealingIntroForm.to_annealing`.
