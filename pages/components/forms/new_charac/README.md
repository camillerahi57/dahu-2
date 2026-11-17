# `pages/components/forms/new_charac/`: form of the new characterization page

The form of `pages/new_charac.py`: a characterization of a film (for now
only EDX), made of its date, author, comment, the film's last
modification before the measurement, and its data file. The data file
(HDF5 for EDX) is read when it is chosen: the form shows what it holds,
and the submit button stays disabled while the file cannot be read. It
builds on `../base_classes.py` (see `../README.md`) and reuses the date,
author and comment fields of `../new_film_modif/fields.py`.

A measurement made on *another* film is not entered here: the library
page references the existing one instead (`CharacReference`).

## Files

- **`fields.py`**: the fields specific to characterizations.
  `CharacTypeField` (which kind), `LastModifField` (the last film
  modification before the measurement, asked explicitly even though the
  dates would let us guess it) and `CharacFileField` (the file picker).
- **`sub_forms.py`**: the forms, and the list of supported kinds.
  - `RootForm` draws `CharacBaseInfoForm`, then the data form of the
    chosen kind. Once valid, its `charac`, `charac_file` and `file_stream`
    attributes are what the page saves: first the file itself
    (`charac_file.save_stream(file_stream)`), then, in a transaction, the
    file's row and the charac with its parts (`save_with_dependent()`).
  - `CharacBaseInfoForm` checks that the dates agree with the chosen last
    modification (the measurement cannot be older than it, nor older than
    the modification that follows it).
  - `CharacDataForm` is the base of the per-kind forms; `EdxForm` reads
    the HDF5 file with `Edx.read_hdf5` and previews the result.
    `read_upload_once` makes sure the file is read once per upload,
    with a progress bar.
  - `CHARAC_TYPES` lists the supported kinds, each with its name, data
    form and drawing function. The library page's banner and dialogs
    use it too.

## Data files are big (several GB)

An EDX file is typically 5 GB, and Streamlit keeps an uploaded file in
memory. What makes the page slow is not the reading of the useful values
but anything that touches *all* the bytes, since the page script reruns
at every click. So:

- **Never** call `getvalue()`, `read()` without a size, `io.BytesIO(...)`
  on the upload, or `st.cache_data` on it (Streamlit hashes the whole
  file at every rerun). Give the upload itself (an open file) to the
  reader: `h5py` reads it in place.
- Read it once per upload with `read_upload_once`, which keeps the small
  result in the session state under the upload's `file_id`.
- Write it to disk with `UserUploadedFile.save_stream` (chunks of 16 MB),
  before the database transaction, which locks the database for everyone.
- In `Edx.read_hdf5`, the time is spent per position and element, not
  per GB: keep the number of h5py calls small (it uses low-level reads
  for the hot loop). About 1 s per 3000 positions.
- The library page never reads the file: the download button gets a
  function (`Path.read_bytes`) that Streamlit calls only when the user
  clicks.

## Common tasks

### Add a new kind of characterization (e.g. MOKE)

1. In `logic/lab_modelization/db_models.py`, add the subtype model (with a
   unique foreign key to `Charac`, and a `delete_parts`), a
   `DependentBackref` list for it in `Charac`, and delete it in
   `Charac.delete_parts`. Write its migration (see
   `logic/migrations/README.md`). The `CharacType` value already exists
   in `db_enums.py` for MOKE, profilometry and VSM/SQUID.
2. In `pages/components/charac_info.py`, add a function drawing the
   subtype's values (like `edx_charac_info`).
3. In `sub_forms.py`, write a `CharacDataForm` subclass (like `EdxForm`):
   a file field, its reading through `read_upload_once` (see the section
   above), its checks, and `attach_to` which sets the subtype list of
   the charac. Add one entry to `CHARAC_TYPES`.
4. Click through the library page ("Add" then the dialog of a saved
   charac) and the new charac page.

### Make characterizations editable

`Charac` has parts (its subtype rows), so an edit page replaces it as a
whole, following "Editing" in `../README.md`. `CharacBaseInfoForm`,
`LastModifField` and `CharacTypeField` already take a `db_default`; keep
the same `CharacFile` row (or delete the old one with its file) when the
file is replaced.
