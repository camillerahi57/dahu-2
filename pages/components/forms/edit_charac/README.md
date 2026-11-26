# `edit_charac/`: form of the "edit characterization" page

The form used by `pages/edit_charac.py` to change a characterization
(`Charac`, for now an EDX) that was already submitted. It has no fields of
its own: it reuses `CharacBaseInfoForm` and the data form of the kind
(`EdxForm`) from `../new_charac/`, prefilled from the existing row, and
`FileLabelField` from `../base_classes.py`.

What can be edited: date, author, last film modification, comment, the
label of the data file, and the data file itself (replaced, or added when
it is missing from the server). The film and the type cannot.

## Files

- **`sub_forms.py`**: `RootForm`, the whole form. Once valid, its
  `charac` (the edited values, with the old id), `file_label`, `new_file`
  (a `CharacFile`, only if a file is given), `file_stream` and
  `new_subtype_rows` (the `Edx` read from the new file) are what the page
  saves.

**The page updates the row in place** (`charac.save()` on an object that
has an id updates that row), so the references other libraries hold to
the characterization stay valid. When the file is replaced, the old
subtype rows are deleted and the new ones inserted; the old file is
removed from `user_data/` only after the transaction succeeded.
