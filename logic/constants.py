from enum import StrEnum
from pathlib import Path


class IdType(StrEnum):
    LIB = 'lib_id'
    FILM = 'film_id'
    TARGET = 'target_id'
    SUB = 'substrate_id'
    STATE = 'state_id'


FILM_INIT_STATE = 'As deposited'
NEW_TARGET = 'NOT BASED ON AN EXISTING TARGET'
PIXEL_COORDS = 'pixel_selection'
REDIRECT_PATH = 'redirect_path'
RESOURCE_TYPE = 'object_type'
OBJ_ID = 'object_id'
DB_UNIT_SYSTEM = 'SI'
ROOM_TEMPERATURE_CELSIUS = 20
USER_DATA_PATH = Path('user_data')


class CookieKeys(StrEnum):
    """Keys are hard coded random strings, so that if we rename the variable
    for an update, we'll still access the value from old version with the
    same key in the cookie."""
    LAST_EMAIL_USED = 'PNCeTLw1LV9bRKmRW2WYb'
    LIB_FILTERS = '1Yp0qXhjE1RdYHi5M79Kq'
    TARGET_FILTERS = 'khHkAiOqfz63PyLktwnOR'
    SUBSTRATE_FILTERS = '4YRQlQPzzFSDyEud0YjSj'


class SessionKeys(StrEnum):
    PATCH_FORMS = 'patch_forms_key'
    SNAP_TO_RESTORE = 'snap_to_restore_key'
    SUBSTRATE_LAYERS = 'substrate_layer_forms_key'
    SUBSTRATE_LAYER_FORMS = 'substrate_layer_forms_key'
    FILM_LAYERS = 'film_layers_key'
    SPUTTERING_SYSTEM = 'sputter_system_key'
    LAYER_DATA = 'additional_layer_data_key'
    CURRENT_FILM = 'current_film_key'
    CURRENT_PATH = 'current_path_key'
    CROPPED_TARGET_IMG = 'cropped_target_key'
    UPLOADED_TARGET_IMG = 'uploaded_target_key'
    IMG_FILE_NAME = 'target_img_name_key'
    CROPPED_PIC = 'cropped_pic_key'
    USE_DEFAULT_TARGET_PIC = 'use_default_target_pic_key'
    USE_DEFAULT_PATTERN = 'use_default_pattern_key'
    PREVIOUS_PIXEL_COORDS = 'previous_pixel_coords_key'
    SELECTED_TARGETS = 'selected_targets_key'
    INSPECT_OBJ_ID = 'switch_page_request_lib_id_key'

    UPLOADED_FILE = 'uploaded_diagram_key'
    FILE_NAME = 'pattern_label_key'
    UPLOADED_AT = 'uploaded_at_key'
    USE_DEFAULT_FILE = 'use_default_file_key'

    LIB_FILTERS = 'lib_filters_key'
    TARGET_FILTERS = 'target_filters_key'
    SUBSTRATE_FILTERS = 'substrate_filters_key'
