"""Functions to make sure DB content is coherent.

`init_page` (in `pages/components/general.py`) calls `get_problems`
when `AppMetadata.next_problem_check_at` has passed and saves each
problem found as an `AppLog` row. They are shown on the home page and on
the logs page.
"""
from datetime import datetime
from typing import Iterable
from zoneinfo import ZoneInfo

from dahu_2_config import NO_RECENT_BACKUP_WARNING_TIMEDELTA
from logic.app_restoration import Snapshot
from logic.constants import DAHU_2_TIMEZONE
from logic.lab_modelization.base_classes import Event
from logic.lab_modelization.db_models import dahu_2_models


def get_problems() -> Iterable[Event]:
    """Run all checks.

    Runs every model's `get_problems()` (unknown enum values, missing
    uploaded files...), then checks that the latest Restic snapshot is
    younger than `NO_RECENT_BACKUP_WARNING_TIMEDELTA`. This is a
    generator: checks run only as the caller iterates over it. Nothing is
    written here; the caller saves the events.

    Side effects: runs the `restic` program (see `Snapshot`), which
    shows a spinner and may write an `AppLog` row if Restic fails.

    Returns:
        The problems found, one `Event` each.
    """
    print("Looking for problems...")

    # Checking in model tables:

    for mod in dahu_2_models:
        for event in mod.get_problems():
            yield event

    # Checking that last backup is relatively recent:

    # With timezone for difference between two tz-aware date-times:
    paris_now = datetime.now(tz=ZoneInfo(DAHU_2_TIMEZONE))
    last_backup_timedelta = paris_now - Snapshot.get_latest().time
    if last_backup_timedelta > NO_RECENT_BACKUP_WARNING_TIMEDELTA:
        yield Event.from_no_recent_backup()

    print("Finished.")
