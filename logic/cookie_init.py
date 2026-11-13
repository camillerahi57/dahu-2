"""Gives access to the browser cookie controller of the current session.

A cookie is a small piece of text that the web browser keeps for a site
and sends back on each visit. Dahu DB uses cookies to remember, per
browser, things like browse filters and the last email address used
(keys in `logic.constants.CookieKeys`).

Call `new_controller()` each time cookies are needed, rather than
building a controller or keeping one in a module-level variable: Python
imports a module once per server process, so such a variable would be
shared by all browser sessions. The first call in a session may wait up
to about 5 s, writes to `st.session_state` and may write `AppLog` rows
(see `new_controller`).
"""
from time import sleep

from streamlit_cookies_controller import CookieController

from logic.lab_modelization.base_classes import Event
from logic.lab_modelization.db_enums import EventType, LogSeverity
from logic.lab_modelization.db_models import AppLog


def new_controller() -> CookieController:
    """Returns the cookie controller of this browser session.

    The controller is stored in `st.session_state` (Streamlit's
    per-browser-tab dictionary that survives reruns, i.e. the re-execution
    of the page script after each user action), so it is created only
    once per session.

    The controller talks to the browser through a hidden component, so
    cookies are not readable right after it is created. The loop writes a
    test cookie, `cookie_ready`, and waits until it can be read back.
    After 5 s it writes a WARNING `AppLog` row on every further
    iteration, but keeps waiting.

    Returns:
        The session's cookie controller.
    """
    from logic.global_variables import sess
    if 'cookie_controller' in sess:
        return sess['cookie_controller']

    controller = CookieController()
    # Stored before the wait loop: the warning below calls
    # `AppLog.save_new`, which calls `new_controller` again and must find
    # this controller instead of creating another one (endless recursion).
    sess['cookie_controller'] = controller
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
            # TODO After 5 s the loop never stops, and writes an
            #   `AppLog` row every 0.1 s until the cookie is readable.

    return controller