from time import sleep

from streamlit_cookies_controller import CookieController

from logic.lab_modelization.base_classes import Event
from logic.lab_modelization.db_enums import EventType, LogSeverity
from logic.lab_modelization.db_models import AppLog


def new_controller() -> CookieController:
    from logic.global_variables import sess
    if 'cookie_controller' in sess:
        return sess['cookie_controller']

    controller = CookieController()
    waited = 0
    while not controller.get('cookie_ready'):
        controller.set('cookie_ready', True)
        sleep(0.1)
        waited += 0.1
        if waited > 5:
            event = Event(
                type=EventType.UI_ERROR,
                notify=False,
                severity=LogSeverity.WARNING,
                description="Cookie feature in user interface is not working "
                            "properly. Cookie could not be loaded.",
            )
            AppLog.save_new(event)

    sess['cookie_controller'] = controller
    return controller


cookies = new_controller()
