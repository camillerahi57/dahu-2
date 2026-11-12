# `pages/components/forms/new_film_modif/lift_off/`: the lift-off form

The part of the film modification form that describes a lift-off. It is
drawn by `RootForm` in `../sub_forms.py` when the user picks "lift-off".
It takes its fields from `../fields.py`, the recipe / pattern form from
`../shared.py`, and its base classes from `../../base_classes.py`.

## Files

- **`sub_forms.py`**: `LiftOffForm`, the whole form: whether ultrasound
  was used and how it was set up, then `EtchingForm` (recipe and
  pattern). `LiftOffForm.to_lift_off_etching` builds the unsaved general
  `Etching` row with its `LiftOffEtching` subtype (a subtype is a separate
  table holding the details of one kind of etching). The
  `default_lift_off` argument would prefill the form from an existing
  lift-off, but no page passes one yet.

**`RootForm` does not list `LiftOffForm` among its sub-forms**, so this
form's validity is only enforced by the `PausePageRun` that
`to_lift_off_etching` raises while it is invalid. Keep that check if you
change the method.
