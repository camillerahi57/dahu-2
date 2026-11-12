# `new_film_modif/ion_beam_etching/`: the ion beam etching form

The part of the film modification form that describes an ion beam etching
(IBE). It is drawn by `RootForm` in `../sub_forms.py` when the user picks
"ion beam etching". It takes its fields from `../fields.py`, the recipe /
pattern form and the gas mixture form from `../shared.py`, and its base
classes from `../../base_classes.py`.

## Files

- **`sub_forms.py`**: `IonEtchingForm`, the whole form. Open it to change
  what is asked about an ion beam etching.
  - `IonEtchingForm.__init__` draws the machine settings (machine,
    durations, flow, angle, rotation, power, pressures, DC grid current),
    then `EtchingForm` (recipe and pattern), then `ConstituentListForm`
    (the plasma gases).
  - `IonEtchingForm.to_ion_etching` builds the unsaved general `Etching`
    row with its `IonBeamEtching` subtype (a subtype is a separate table
    holding the details of one kind of etching) and its plasma
    constituents.

  Each value is typed in the UI unit of its field class (e.g. SCCM for the
  flow, degrees for the angle, rpm for the rotation) and stored in SI base
  units (m³/s, rad, rad/s). The `default_beam_etch` argument would prefill
  the form from an existing etching, but no page passes one yet.

## Common tasks

### Add a machine setting

1. Add the column to `IonBeamEtching` in
   `logic/lab_modelization/db_models.py` and write its migration (see
   `logic/lab_modelization/README.md`).
2. Add the field class to `../fields.py`.
3. In `sub_forms.py`, draw it in `IonEtchingForm.__init__`, store its
   value, add the field to the `fields=[...]` list of `super().__init__`,
   and pass the value to `IonBeamEtching(...)` in `to_ion_etching`.
