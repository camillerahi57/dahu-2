# `pages/components/forms/new_substrate/`: form of the substrate pages

The form of `pages/new_substrate.py` and `pages/edit_substrate.py`: a
substrate's name, comment, and its stack of layers (composition, thickness
and crystal orientation of each). It is the smallest form package, so it
is a good example of how `fields.py` and `sub_forms.py` work together. It
builds on `../base_classes.py`.

## Files

- **`fields.py`**: one class per input. `SubstrateLabelField` (unique
  name; on the edit page the substrate's own current name is allowed),
  `StoichiometryField` (chemical formula of a layer), `ThicknessField`
  (typed in µm, stored in m), `HField` / `KField` / `LField` (Miller
  indices), `LayerCountField`.
  `pages/inspect_substrate.py` also uses `ThicknessField` to display
  stored thicknesses.
- **`sub_forms.py`**: the forms, nested as `RootForm` → `LayerListForm` →
  one `LayerForm` per layer (bottom first) → `CrystalOrientationForm`.
  - `RootForm.to_substrate` builds the unsaved `Substrate` with its
    `SubstrateLayer`s, which the page saves with `save_with_dependent()`.
    The edit page passes the old id so the substrate keeps it.
  - `RootForm.show_layers` draws a sketch of the stack, top layer first.
  - `CrystalOrientationForm` refuses the orientation (0, 0, 0).

On the edit page each form gets the existing substrate or layer as its
default, so its fields are prefilled. **The edit page replaces the
substrate as a whole**: it deletes the old row and its layers, then
inserts the new ones with the old substrate id, in one transaction (a
group of database writes that all succeed or are all cancelled).

## Common tasks

### Add a property to substrate layers

1. Add the column to `SubstrateLayer` in
   `logic/lab_modelization/db_models.py` and write its migration (see
   `logic/lab_modelization/README.md`).
2. Add a field class to `fields.py` (subclass `UnitField` and set
   `ui_unit` for a physical quantity, like `ThicknessField`).
3. In `sub_forms.py`, draw it in `LayerForm.__init__`, passing the
   form's `key` (the layer index) and `db_default=` the existing layer's
   value. The key matters: the same field class appears once per layer,
   and two widgets with the same key make Streamlit raise an error. Store
   its value and add the field to the list given to `super().__init__`.
4. Pass the value on in `RootForm.to_substrate`, which builds each layer
   with `SubstrateLayer.from_stoichio(...)`; add a parameter to that
   method in `db_models.py`.
