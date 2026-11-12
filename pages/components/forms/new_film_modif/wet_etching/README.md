# `pages/components/forms/new_film_modif/wet_etching/`: the wet etching form

The part of the film modification form that describes a wet (chemical)
etching. It is drawn by `RootForm` in `../sub_forms.py` when the user picks
"wet etching". It takes its fields from `../fields.py`, the recipe /
pattern form from `../shared.py`, and its base classes from
`../../base_classes.py`.

## Files

- **`sub_forms.py`**: the wet etching forms. Open it to change what is
  asked about a wet etching.
  - `WetEtchingForm`: development time, hard bake temperature, base and
    acid, solvents, ultrasound, etching speeds, then `EtchingForm` (recipe
    and pattern). Times are typed in min and temperatures in °C, speeds in
    µm/s; they are stored in s, K and m/s.
  - `WetEtchingForm.to_wet_etching`: builds the unsaved general `Etching`
    row with its `WetEtching` subtype (a subtype is a separate table
    holding the details of one kind of etching) and its solvents.
  - `SolventListForm`: the number of solvents, then one `SolventField`
    each, in order of use; `to_solvents` builds the `EtchingSolvent` rows.

  The `default_wet_etch` argument would prefill the form from an existing
  etching, but no page passes one yet.

**`RootForm` does not list `WetEtchingForm` among its sub-forms**, so this
form's validity is only enforced by the `PausePageRun` that
`to_wet_etching` raises while it is invalid. Keep that check if you change
the method.

## Common tasks

### Offer a new acid, base or solvent in the lists

1. Add a member to `EtchingAcidSuggestion`, `EtchingBaseSuggestion` or
   `EtchingSolventSuggestion` in `logic/lab_modelization/db_enums.py`.
   These lists are only suggestions: users can already type any name.
