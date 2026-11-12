# `pages/components/forms/new_target/`: forms of the target pages

The form of the "new target" page (`pages/new_target.py`). A target is
recorded with its first *deterioration state*: a cropped photo of the
target, the photo's scale, and the patches (pieces of material placed on
the target to tune its composition) drawn as polygons in pixel
coordinates on that photo. `BasicInfoForm` is reused by
`pages/edit_target.py`, and `DeteriorationStateForm` by
`../new_deterioration_state/` and `../edit_deterioration_state/`. It
builds on `../base_classes.py` and uses `../../pixel_helper.py` to read
pixel coordinates on the photo.

## Files

- **`fields.py`**: one class per input. Open it to change a label or a
  validation rule. Examples: `TargetLabelField`, `PreviousVersionField`
  (the target this one was made from, or "new target"),
  `PhotoUploadField` (JPG or PNG), `PixelEquivalenceField` with
  `MillimeterEquivalenceField` (a length measured on the photo, giving
  its scale), `ShapeField` and `CoordinateField` (shape and `"X, Y"`
  points of a patch), `IsBasePatchField` (the bulk target material under
  every other patch).
- **`sub_forms.py`**: the forms, from the outside in:
  - `RootForm`: the whole page, `BasicInfoForm` then
    `DeteriorationStateForm`. Its `target` attribute is the unsaved
    `Target` with its state, photo and patches.
  - `BasicInfoForm`: label, date, author email (prefilled from a cookie,
    a small value the browser keeps for the site) and previous version;
    `to_target` builds the `Target` row.
  - `DeteriorationStateForm`: `StateForm` (photo, date, scale,
    calibration, comment), then `PatchListForm`, a figure of the patches
    and a "the figure is right" confirmation.
  - `UploadAndCropForm`: upload, then crop the photo. It is a small
    *state machine* (a form whose step is remembered between reruns, in
    the session state): no photo → uploader; uploaded → cropper;
    cropped → preview.
  - `PatchListForm` → one `PatchForm` per patch → `DiscPatchForm` (3
    points on the circle) or `PolygonPatchForm` (the vertices). There must
    be exactly one base patch, first in the list. A disc is stored as a
    polygon (`PatchForm.to_patch`).

Streamlit runs the page script again from the top after every click (a
*rerun*); values that must survive reruns, such as the uploaded and the
cropped photo, are kept in the session state (`st.session_state`, a
dictionary kept per browser tab).

## Common tasks

### Add a piece of basic information to targets

1. Add the column to `Target` in `logic/lab_modelization/db_models.py`
   and write its migration (see `logic/lab_modelization/README.md`).
2. Add a field class to `fields.py`.
3. In `sub_forms.py`, draw it in `BasicInfoForm.__init__` with
   `db_default=` the value of `default_target` (so the edit target page is
   prefilled), store its value, and add it to the `fields=[...]` list of
   `super().__init__`.
4. Pass the value to `Target(...)` in `BasicInfoForm.to_target`. Both the
   new and the edit target pages then handle it.
