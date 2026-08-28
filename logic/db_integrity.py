"""Functions to make sure DB content is coherent."""
from datetime import datetime
from typing import Iterable
from zoneinfo import ZoneInfo

from dahu_2_config import NO_RECENT_BACKUP_WARNING_TIMEDELTA
from logic.app_restoration import Snapshot
from logic.constants import DAHU_2_TIMEZONE
from logic.lab_modelization.base_classes import Event
from logic.lab_modelization.db_models import dahu_2_models


def get_problems() -> Iterable[Event]:
    """Run all checks."""
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
