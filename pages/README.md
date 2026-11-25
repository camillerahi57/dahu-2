# `pages/`: the web pages of the app

One Python file per web page, plus `entry_point.py`, the script that
`streamlit run` starts. Each page draws itself with Streamlit, using the
shared UI code and forms in `components/`, and reads or writes the
database through the models in `logic/lab_modelization/`. Every page is
registered in `logic/page_list.py`, which gives it its URL and title.

A few words used below:

- **Rerun**: Streamlit runs the whole page script again, from the top,
  after every click or widget change.
- **Session state** (`st.session_state`, shortened to `sess`): a
  dictionary Streamlit keeps for each browser tab across reruns.
- **Query parameter**: a `name=value` pair at the end of a page's URL. A
  page that shows one object finds it there, e.g. `inspect_lib?lib_id=3`.
  The names are the values of `IdType` in `logic/constants.py`.
- **Transaction** (`with db.atomic():`): a group of database writes that
  all succeed or are all cancelled.
- **Dialog**: a pop-up window, drawn by a function decorated with
  `@st.dialog`.

**Rules for page files** (the shared code in `components/` is not
concerned):

- **A bare string anywhere except as the first statement of the module,
  a function or a class is displayed on the web page** (Streamlit's
  "magic"). Write `#` comments instead.
- **Never import a page file from another module.** Streamlit runs pages
  as scripts, so the import runs the page a second time inside the
  current one. Put shared code in `components/`. (`browse_patterns.py`
  is currently imported by `components/browsing.py`; see the `TODO`
  there.)
- Every page starts with `init_page(pages.<its own entry>)` and wraps
  its body in `try: ... except PausePageRun: pass`. `init_page` clears
  the session state when the page name changes, so pass the page's own
  entry. (`edit_substrate.py` passes `pages.new_substrate`; see the
  `TODO` there.)
- Opening any page may start a Restic backup and the periodic problem
  check (see `init_page` in `components/general.py`).

## Subfolders

- **`components/`**: UI code shared between pages, including every input
  form (`components/forms/`). See its `README.md`.

## Files

### Start-up

- **`entry_point.py`**: the main script, given to `streamlit run`. On
  every run it checks that `user_data/dahu_2.db` exists and has tables,
  then `st.navigation` runs the page matching the URL (`browse_libs.py`
  when there is none). In production it shows a page's error on the web
  page; in development it raises it, so the full traceback appears.
  Don't import it.

### Browsing (the tables, with a sidebar instead of a Home button)

- **`browse_libs.py`**: the home page. All libraries, most recently
  inspected first, with filters saved in a cookie (a small text the
  browser keeps between visits) and the banner of unread log warnings
  (`problem_banner`).
- **`browse_targets.py`**, **`browse_substrates.py`**: the tables of
  sputtering targets and substrates. Same mechanisms as `browse_libs.py`.
- **`browse_patterns.py`**: the uploaded pattern files (lithography mask
  designs). Also defines the show, rename and delete dialogs
  (`show_delete_dialog`, `show_rename_dialog`) used for both patterns
  and recipes. A file used by an etching can't be deleted.
- **`browse_recipes.py`**: the uploaded etching recipe files.

### Inspecting one object

- **`inspect_library.py`**: one library: its film modifications and
  characterizations (each opens a dialog with its details, a download
  button for its data file, and Edit and Delete buttons, or a Remove
  reference button for a measurement made on another film), its uploaded
  files,
  the film and its layer table. Archive, Edit and Delete buttons.
  Opening it updates `Library.last_inspected_at`, the sort order of the
  home page. Key
  functions: `page_body`, `film_modif_info`, `charac_section`,
  `charac_dialog`, `add_charac_dialog`, `confirm_deletion_dialog`.
- **`inspect_target.py`**: one target and its deterioration states (photo
  and patches), most recent first. Archive, edit, delete the target; add,
  edit, delete states. Key functions: `main_page`, `show_state`,
  `confirm_deletion_dialog`.
- **`inspect_substrate.py`**: one substrate and its layers. It can only
  be deleted when no film was deposited on it.

### Adding objects (forms from `components/forms/new_*/`)

Each builds an unsaved object with its parts (child rows) from the form's
`RootForm`, saves it with `save_with_dependent()` in a transaction, then
calls `switch_to_submit_successful`.

- **`new_lib.py`**: a library with its film, targets used and layers.
- **`new_target.py`**: a target with its first deterioration state.
- **`new_deterioration_state.py`**: a new state of an existing target
  (`target_id`).
- **`new_substrate.py`**: a substrate and its layers. The shortest
  example of a "new" page.
- **`new_film_modif.py`**: an annealing or etching of a film
  (`film_id`).
- **`new_charac.py`**: a characterization (e.g. an EDX) made on a film
  (`film_id`), with its HDF5 data file (several GB: see the README of
  `components/forms/new_charac/`). Reached from the "Add" button of
  the library page's "Characterisations" banner; a measurement made on
  *another* film is referenced from that banner's dialog instead.
- **`new_lib_file_upload.py`**: a file of any format for a library
  (`lib_id`).
- **`new_pattern.py`** (PNG or JPEG only), **`new_recipe.py`**: pattern
  and recipe files. Each defines a small `FileUploadForm` subclass
  (`PatternUploadForm`, `RecipeUploadForm`) that refuses a label already
  used.

### Editing objects

Edit pages reuse the forms of the "new" pages, prefilled from the object.

- **`edit_lib.py`** (`lib_id`), **`edit_film.py`** (`film_id`),
  **`edit_target.py`** (`target_id`): update one row in place; the id is
  kept.
- **`edit_substrate.py`** (`substrate_id`): deletes the substrate and its
  layers, then inserts the new ones with the old substrate id.
- **`edit_film_layers.py`** (`film_id`): deletes every layer of the film
  with its parts, then saves the new ones. **The layers get new ids.**
- **`edit_deterioration_state.py`** (`state_id`): deletes the state with
  its patches and photo, then saves the new one. **The state gets a new
  id, and its photo a new file in `user_data/`.**
- **`edit_charac.py`** (`charac_id`): updates the characterization row in
  place (the id is kept, so references from other libraries stay valid).
  The film and the type cannot change. If the data file is replaced (or
  added, when it is missing from the server), the EDX rows are deleted and
  read again from the new file, and the old file is deleted once the
  transaction has succeeded. Reached from the "✏️ Edit" link of the
  library page's characterization dialog.

### Other pages

- **`submission_successful.py`**: the confirmation shown after a form
  was saved, with a "Continue" button to the page given by
  `switch_to_submit_successful`.
- **`view_logs.py`**: the `AppLog` rows (saves, deletions, backups,
  problems found by the periodic check), newest first, with filters,
  pages of rows and a CSV download. A warning leaves the home page banner
  once marked read, a critical error once marked solved.
- **`admin.py`**: link to the logs, Excel (XLSX) export of the whole
  database, and restoration of a backup. **Restoring a snapshot replaces
  the whole `user_data/` folder (database and uploaded files) for every
  user, and deletes every snapshot taken after it.** It asks for the
  password in the `dahu_admin_password` environment variable.
- **`test.py`**: a scratch page for developers (registered as "Test
  Page"). It reads the database and prints to the console. Not part of
  the app's documentation; leave it as is.

**Deleting a library deletes its film's own characterizations, with
their data files** (for good). It is refused while another library uses
one of them as a reference (see `Library.dependent_libraries`).

## Common tasks

### Add a page

1. Create `pages/<name>.py` with a module docstring. Start it with
   `init_page(pages.<name>)` and wrap its body in
   `try: ... except PausePageRun: pass`.
2. Register it in `logic/page_list.py`: add an attribute to `_Pages` with
   `Page('../pages/<name>.py', url_path=..., title=..., icon=...)`.
   **Never change an existing `url_path`**: saved links and bookmarks
   would break.
3. Link to it with `switch_page_bttn(pages.<name>, ...)` from
   `components/general.py`, passing `q_params` if it shows one object.
4. List it in this README.

### Add a "new" page for a new kind of object

1. Write the form package `components/forms/new_<thing>/` (see
   `components/forms/README.md`).
2. Copy `new_substrate.py`: draw `RootForm`, show
   `st.button("Submit", disabled=not root_form.is_valid)`, and on click
   save inside `with db.atomic():`, then call
   `switch_to_submit_successful(redirect_to=..., id_type=IdType.X,
   object_id=obj.id)`.
3. Register and link the page as in "Add a page".

### Add an edit page

1. Read the object's id with `current_params()[IdType.X]` and load it.
2. Build the same `RootForm` with the object as default, so its fields
   are prefilled.
3. On Submit: for an object without parts, rebuild it with the old id and
   call `save()`. For an object with parts, inside `with db.atomic():`,
   call `old.delete_with_parts()`, then
   `new.save_with_dependent(force_insert=True)` (see `edit_substrate.py`
   and the comment there).
