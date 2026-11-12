# `pages/components/`: UI code shared between pages

Everything that more than one page draws: page start-up, navigation
buttons and links, the sidebar of the browsing pages, the header of the
inspect pages, and all the input forms (`forms/`). The page files in
`pages/` import from here; this folder imports from `logic/` (models,
constants, page list, backups). Import it as `from components.… import …`
(never `pages.components…`): Streamlit puts `pages/` itself on Python's
import path.

**Never import a page file (`pages/*.py`) from here.** Streamlit runs
pages as scripts, so importing one runs its code a second time inside the
current page (a "double page load"). Put the shared code here instead.
`file_row` in `browsing.py` currently breaks this rule (see the `TODO`
there).

A few words used below:

- **Rerun**: Streamlit runs the whole page script again, from the top,
  after every click.
- **Session state** (`st.session_state`, shortened to `sess`): a
  dictionary Streamlit keeps for each browser tab across reruns.
- **Query parameter**: a `name=value` pair at the end of a page's URL
  (e.g. `?lib_id=3`), which tells a page which object to show.
- **Callback**: a function Streamlit calls when a widget is used, before
  rerunning the page.
- **Dialog**: a pop-up window, drawn by a function decorated with
  `@st.dialog`.

## Subfolders

- **`forms/`**: every input form of the app (fields, forms, and one
  package per kind of object). Open it for anything the user fills in.
  See its `README.md`.

## Files

- **`general.py`**: helpers used by every page. Open it to understand how
  a page starts or how to link to another page.
  - `init_page`: called first by every page. Starts a Restic backup in a
    background thread (a task running at the same time as the page) when
    one is due, runs the periodic problem check, draws the Home button,
    and clears the app's session state entries when the user comes from
    another page.
  - `switch_page_bttn`: a button to another page. When the current URL
    has query parameters it draws an HTML link instead, because
    `st.switch_page` would break the browser's back button.
  - `switch_to_submit_successful`: what a form page calls after saving.
  - `current_params`: the query parameters of the current URL.
  - Smaller helpers: `show_html_link` and `st_page_link_html` (links with
    absolute URLs built from `DOMAIN` in `dahu_2_config.py`), `icon`,
    `colored`, and date formatting (`extensive_date_str`...).
- **`browsing.py`**: pieces of the browsing pages (the tables of
  libraries, targets, substrates, patterns and recipes).
  `browser_side_bar` draws the sidebar, which replaces Streamlit's own
  page navigation (turned off); `on_inspect_click` is the callback of the
  "Inspect" button column; `file_row` draws one pattern or recipe with its
  buttons.
- **`inspection.py`**: pieces of the inspect pages (one library, target
  or substrate). `inspect_page_header` draws the title with the Edit and
  Delete buttons; `show_film_layer` is the dialog showing one layer of the
  library page's layer table.
- **`library_files.py`**: the "Uploaded Files" box of the library page.
  `file_list_container` draws the list and its Add button;
  `delete_dialog` deletes a file (database row and file in `user_data/`)
  after confirmation.
- **`pixel_helper.py`**: the "Pixel Helper" dialog, where the user clicks
  on the target photo to read pixel coordinates and the distance between
  two clicks. Used by the target forms (`forms/new_target/`) for the
  photo scale and the patch coordinates. `pixel_helper_button` draws the
  button, `show_pixel_helper` the dialog.

**Don't use `close_button` in `general.py`.** It simulates Ctrl+W on the
computer running the server, not on the user's computer. Nothing calls it
at the moment.

## Common tasks

### Add a button that opens another page

1. Call `switch_page_bttn(pages.<name>, label=..., q_params={...})`
   from `general.py`. Put the object's id in `q_params` under its
   `IdType` name (e.g. `{IdType.LIB: lib.id}`).
2. If two buttons on the page have the same label, also pass a distinct
   `key`.

### Add a page to the sidebar of the browsing pages

1. Add `pages.<name>` to the `sidebar_pages` list in `browser_side_bar`
   (`browsing.py`).
