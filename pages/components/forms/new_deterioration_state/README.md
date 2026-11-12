# `new_deterioration_state/`: form of the "new deterioration state" page

The form used by `pages/new_deterioration_state.py` to record a new
deterioration state of an existing target: a dated photo of the target
with the patches (pieces of material placed on it) drawn on the photo.
The state itself (photo, scale, patches) is asked by
`DeteriorationStateForm` from `../new_target/`; this package only adds the
author and a check that the change is really wear.
`../edit_deterioration_state/` reuses its `MadeByField`.

## Files

- **`fields.py`**: the two fields specific to this page.
  - `MadeByField`: email address of who records the state; a select box
    of the known addresses that also accepts a new one.
  - `IsItReallyDeteriorationField`: "is this due to wear, or to a human
    intervention?". Not stored. A human intervention (cleaning, new
    patch...) must be recorded as a new target instead.
- **`sub_forms.py`**: `RootForm`, the whole form: the title, the wear
  question, the author, then `DeteriorationStateForm`. Its `state`
  attribute is the unsaved `DeteriorationState` with its patches and
  photo, which the page saves with `save_with_dependent()`.
