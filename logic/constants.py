"""Constants shared by the whole app: names of query parameters, session
state keys and cookie keys, plus a few fixed values and paths.

A few words used below:

- Query parameter: a `name=value` pair at the end of a page's URL, e.g.
  `?lib_id=3`. Pages use them to know which object to show.
- Session state (`st.session_state`): a dictionary that Streamlit keeps
  for each browser tab. It survives reruns (Streamlit re-executes the
  page script after every click) but is lost when the tab is closed.
- Cookie: a small piece of text stored by the browser, so it survives
  closing the tab.
- Enum (`StrEnum`): a fixed list of named constants whose values are
  strings. They compare equal to plain strings, so `IdType.LIB` can be
  used wherever the string `'lib_id'` is expected.
"""

from enum import StrEnum
from pathlib import Path


# TODO Delete unused keys and constants?


class IdType(StrEnum):
    """Names of the query parameters that address one object.

    A page finds its object with e.g. `current_params()[IdType.LIB]`, and
    links to a page add e.g. `?lib_id=<id>` to the URL.
    """
    LIB = 'lib_id'  # A `Library`.
    FILM = 'film_id'  # A `Film`.
    TARGET = 'target_id'  # A `Target`.
    SUB = 'substrate_id'  # A `Substrate`.
    STATE = 'state_id'  # A target's `DeteriorationState`.


# Option of the "made after" selectbox of the film modification form that
# stands for "no modification yet". It is a (modification number, label)
# couple, like the other options. Number 0 is the film as deposited.
FILM_INIT_STATE = (0, 'Initial state (as deposited)')
# Option of the "previous version" selectbox of the target form: the new
# target is not a new version of an existing one (`previous_version` is
# then NULL in the DB).
NEW_TARGET = 'Not based on an existing target'
# Widget key of the image-click component of the pixel helper dialog.
PIXEL_COORDS = 'pixel_selection'
# The three names below are query parameters of the "submission
# successful" page (see `switch_to_submit_successful`): the URL path of
# the page to go to next, and the kind (an `IdType` value) and id of the
# object that page should show.
REDIRECT_PATH = 'redirect_path'
RESOURCE_TYPE = 'object_type'
OBJ_ID = 'object_id'
# Time zone of the lab, used wherever timezone-aware dates are compared.
DAHU_2_TIMEZONE = 'Europe/Paris'
# Name of the Pint unit system that the DB uses: SI, so that the
# quantities are stored in SI base units (m, s, K, kg...).
DB_UNIT_SYSTEM = 'SI'
# Temperature, in degrees Celsius, that is assumed when a step of an
# annealing is flagged "room temperature" (no temperature is stored).
ROOM_TEMPERATURE_CELSIUS = 20
# Paths are relative to the working directory, so the app must be started
# from the repository root.
DB_PATH = Path('user_data/dahu_2.db')  # The SQLite database file.
USER_DATA_PATH = Path('user_data')  # DB and all uploaded files.
# Number of log entries per page on the logs page.
LOG_PAGE_LENGTH = 50


class CookieKeys(StrEnum):
    """Keys are hard coded random strings, so that if we rename the variable
    for an update, we'll still access the value from old version with the
    same key in the cookie.

    Each key stores, per browser, the last value entered or chosen by the
    user. Never change the string values.
    """
    LAST_EMAIL_USED = 'PNCeTLw1LV9bRKmRW2WYb'  # Pre-fills email fields.
    # Last filters chosen on the three browsing pages.
    LIB_FILTERS = '1Yp0qXhjE1RdYHi5M79Kq'
    TARGET_FILTERS = 'khHkAiOqfz63PyLktwnOR'
    SUBSTRATE_FILTERS = '4YRQlQPzzFSDyEud0YjSj'


class SessionKeys(StrEnum):
    """Keys used in `st.session_state` (`sess`) by the pages and forms.

    `init_page` deletes all the keys of this enum from the session state
    when the user arrives from another page (`logic.utils.reset_session`),
    so the values below only live while one page is used. Some keys are
    used as a prefix: a form that can appear several times adds its own
    `key` to them (e.g. `Sk.UPLOADED_FILE + key`).
    """
    # TODO Probably leftovers: no code uses the six keys below any more. (The
    # second and third have the same string value, so Python makes
    # `SUBSTRATE_LAYER_FORMS` an alias, i.e. another name, of
    # `SUBSTRATE_LAYERS`.)
    PATCH_FORMS = 'patch_forms_key'
    SUBSTRATE_LAYERS = 'substrate_layer_forms_key'
    SUBSTRATE_LAYER_FORMS = 'substrate_layer_forms_key'
    FILM_LAYERS = 'film_layers_key'
    SPUTTERING_SYSTEM = 'sputter_system_key'
    LAYER_DATA = 'additional_layer_data_key'
    # The `Film` being inspected or modified, read by the film
    # modification form to list the film's existing modifications.
    CURRENT_FILM = 'current_film_key'
    # URL path of the page currently shown, to detect a page change.
    CURRENT_PATH = 'current_path_key'

    # Target photo upload (`UploadAndCropForm`):
    CROPPED_TARGET_IMG = 'cropped_target_key'  # Cropped image (PIL).
    UPLOADED_TARGET_IMG = 'uploaded_target_key'  # Uploaded bytes.
    IMG_FILE_NAME = 'target_img_name_key'  # Original file name.
    CROPPED_PIC = 'cropped_pic_key'  # Widget key of the cropper.
    # True while the photo of the edited state may be preloaded; set to
    # False once the user deletes it.
    USE_DEFAULT_TARGET_PIC = 'use_default_target_pic_key'

    # Only used in commented-out code (the old pattern diagram form).
    USE_DEFAULT_PATTERN = 'use_default_pattern_key'
    # (x, y) of the last click in the pixel helper.
    PREVIOUS_PIXEL_COORDS = 'previous_pixel_coords_key'
    # Labels of the targets chosen in the library form, offered by
    # `TargetChoiceField`.
    SELECTED_TARGETS = 'selected_targets_key'
    # Id of the row whose "inspect" button was clicked in a browsing page.
    # (Its string value still says "lib_id" although all browsing pages
    # use it.)

    # TODO has the value
    #   `'switch_page_request_lib_id_key'` although all three browsing pages
    #   use it. Is the name left from when only libraries had an inspect
    #   button?
    INSPECT_OBJ_ID = 'switch_page_request_lib_id_key'

    # Generic file upload (`FileUploadForm`). Used as prefixes: the
    # form's `key` is appended.
    UPLOADED_FILE = 'uploaded_diagram_key'  # File content (bytes).
    FILE_NAME = 'pattern_label_key'  # Original file name.
    UPLOADED_AT = 'uploaded_at_key'  # Upload date-time.
    # True while the existing file may be preloaded; set to False once
    # the user cancels it.
    USE_DEFAULT_FILE = 'use_default_file_key'

    # Filters of the browsing pages: the `filters_name` of the
    # `DynamicFilters` widgets, saved in the cookies of the same name in
    # `CookieKeys`.
    LIB_FILTERS = 'lib_filters_key'
    TARGET_FILTERS = 'target_filters_key'
    SUBSTRATE_FILTERS = 'substrate_filters_key'

    LOG_PAGE = 'log_page_key'  # Index (from 0) of the page of logs shown.
    # Snapshot chosen on the admin page and waiting for the restore
    # confirmation.
    SNAP_TO_RESTORE = 'snap_to_restore_key'
