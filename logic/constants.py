from enum import StrEnum
from pathlib import Path


class IdType(StrEnum):
    LIB = 'lib_id'
    FILM = 'film_id'
    TARGET = 'target_id'
    SUB = 'substrate_id'
    STATE = 'state_id'


DOMAIN = 'localhost:8501'
FILE_STORAGE_PATH = Path(
    r"C:\Users\Camille.RAHI\Documents\Documents\Code\dahu-2-storage")
FILM_INIT_STATE = 'As deposited'
PATTERN_IMAGE_PATH = 'pages/logic/images'
NEW_TARGET = 'NOT BASED ON AN EXISTING TARGET'
PIXEL_COORDS = 'pixel_selection'
REDIRECT_PATH = 'redirect_path'
RESOURCE_TYPE = 'object_type'
OBJ_ID = 'object_id'
DB_UNIT_SYSTEM = 'SI'
ROOM_TEMPERATURE_CELSIUS = 20
USER_UPLOAD_PATH = Path('user_uploads')


class EtchingPattern(StrEnum):
    pattern_2025_02_19 = 'pattern_2025_02_19.png'


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
    SUBSTRATE_LAYERS = 'substrate_layer_forms_key'
    SUBSTRATE_LAYER_FORMS = 'substrate_layer_forms_key'
    FILM_LAYERS = 'film_layers_key'
    SPUTTERING_SYSTEM = 'sputter_system_key'
    LAYER_DATA = 'additional_layer_data_key'
    CURRENT_FILM = 'current_film_key'
    CURRENT_PATH = 'current_path_key'
    CROPPED_TARGET_IMG = 'cropped_target_key'
    UPLOADED_TARGET_IMG = 'uploaded_target_key'
    UPLOADED_FILE = 'uploaded_diagram_key'
    TARGET_IMG_NAME = 'target_img_name_key'
    CROPPED_PIC = 'cropped_pic_key'
    USE_DEFAULT_TARGET_PIC = 'use_default_target_pic_key'
    FILE_NAME = 'pattern_label_key'
    UPLOADED_AT = 'uploaded_at_key'
    USE_DEFAULT_PATTERN = 'use_default_pattern_key'
    PREVIOUS_PIXEL_COORDS = 'previous_pixel_coords_key'
    SELECTED_TARGETS = 'selected_targets_key'
    INSPECT_OBJ_ID = 'switch_page_request_lib_id_key'

