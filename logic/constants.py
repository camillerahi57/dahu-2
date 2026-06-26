from enum import StrEnum
from pathlib import Path


LIB_ID_URL_KEY = 'lib_id'
FILM_ID_URL_KEY = 'film_id'
TARGET_ID_URL_KEY = 'target_id'
STATE_ID_URL_KEY = 'state_id'
SUB_ID_URL_KEY = 'substrate_id'
DOMAIN = 'localhost:8501'
FILE_STORAGE_PATH = Path(
    r"C:\Users\Camille.RAHI\Documents\Documents\Code\dahu-2-storage")
FILM_INIT_STATE = 'As deposited'
PATTERN_IMAGE_PATH = 'pages/logic/images'
NEW_TARGET = 'NOT BASED ON AN EXISTING TARGET'
PIXEL_COORDS = 'pixel_selection'
REDIRECT_PATH_URL_KEY = 'redirect_path'
ID_KEY_URL_KEY = 'id_key'
ID_VALUE_URL_KEY = 'id_value'
DB_UNIT_SYSTEM = 'SI'
ROOM_TEMPERATURE_CELSIUS = 20

class CookieKeys(StrEnum):
    """Keys are hard coded random strings, so that if we rename the variable
    for an update, we'll still access the value from old version with the
    same key in the cookie."""

    LAST_EMAIL_USED = '4f89qv6sdw531xcs6qqf4c5q6d8zs4cD'
    LIB_FILTERS = 'f4ze86sd4ce1v68rrf46sdw1cqz568fc4'
    TARGET_FILTERS = 'd48qz6f4cdsv1r3e54g68e6rq43q1dz'
    SUBSTRATE_FILTERS = 'e46vsq98f4z5618af9ez4sxdq4658f4s'


class SessionKeys(StrEnum):
    PATCH_FORMS = 'patch_forms_key'
    PAGE_URL_PATH = 'page_url_path_key'
    SUBSTRATE_LAYERS = 'substrate_layer_forms_key'
    SUBSTRATE_LAYER_FORMS = 'substrate_layer_forms_key'
    FILM_LAYERS = 'film_layers_key'
    SPUTTERING_SYSTEM = 'sputter_system_key'
    LAYER_DATA = 'additional_layer_data_key'
    CURRENT_FILM = 'current_film_key'
    CROPPED_TARGET_IMG = 'cropped_target_key'
    UPLOADED_TARGET_IMG = 'uploaded_target_key'
    TARGET_IMG_NAME = 'target_img_name_key'
    CROPPED_PIC = 'cropped_pic_key'
    USE_DEFAULT_TARGET_PIC = 'use_default_target_pic_key'
    PREVIOUS_PIXEL_COORDS = 'previous_pixel_coords_key'
    SELECTED_TARGETS = 'selected_targets_key'


