# `edit_deterioration_state/`: form of the "edit deterioration state" page

The form used by `pages/edit_deterioration_state.py` to change a target's
deterioration state (a dated photo of the target with its patches). It
has no fields of its own: it reuses `MadeByField` from
`../new_deterioration_state/` and `DeteriorationStateForm` from
`../new_target/`, prefilled from the existing state.

## Files

- **`sub_forms.py`**: `RootForm`, the whole form. It is the "new
  deterioration state" form without the "is it really wear?" question.
  Its `state` attribute is the new, unsaved `DeteriorationState` with its
  patches and photo; `target_img` is the cropped photo.

**The page replaces the state as a whole**: it deletes the old state with
its patches and photo file, then saves the new one. The new state gets a
new id and its photo a new file in `user_data/`, so links that contained
the old `state_id` no longer work.
