# `edit_film_layers/`: form of the "edit film layers" page

The form used by `pages/edit_film_layers.py` to change the targets and
layers of an existing film. It has no fields of its own: it reuses
`TargetListForm`, `LayerListForm` and `ConfirmOrderField` from
`../new_library/`, prefilled from the film.

## Files

- **`sub_forms.py`**: `RootForm`: the list of targets used, the layer
  list, and the "layer order is right" checkbox. Its `layers` attribute
  holds the new, unsaved `FilmLayer`s, bottom first, with their parts
  (the rows each layer owns: its sputtering details, its target uses and
  its nominal composition).

**The page replaces every layer of the film**: it deletes the old layers
with their parts, then saves the new ones, which get new ids.

## Common tasks

### Add a layer parameter

1. Follow "Add a parameter to a layer" in `../new_library/README.md`:
   this form uses the same layer forms, so nothing changes here.
