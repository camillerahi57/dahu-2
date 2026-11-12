# `pages/components/forms/new_charac/`: empty, for a future form

This folder holds no code, and nothing in the app refers to it. Its name
follows the `new_<thing>/` pattern of the other form packages, so it is
presumably meant for a "new characterization" form, which does not exist
yet: the "Add" button of the characterizations on the library page
(`charac_section` in `pages/inspect_library.py`) still points to the home
page, with a comment saying it should open a "new charac" page. The EDX
characterization feature is still in development.

## Common tasks

### Write the "new characterization" form here

1. Create `fields.py` (one `Field` subclass per input) and `sub_forms.py`
   ending with a `RootForm`, following `../new_substrate/` as a small
   example. See `../README.md` for how fields and forms work.
2. List both files in this README.
