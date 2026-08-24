from datetime import timedelta
from enum import IntEnum

DOMAIN = 'localhost:8501'  # URL of the DAHU 2 app on Neel's network
# (IP address with port number).
RESTIC_PASSWORD = 'no_password'  # Password of the Restic repository, probably
# 'no_password' as suggested in the Dahu 2 setup manual.
RESTIC_REPO_PATH = r'O:\DAHU2\dev\backups\restic_snapshot_repo'  # Path to the
# Restic repository (on the server where the backups are stored).
DAHU_2_CODE_BASE_PATH = r'C:\Users\Camille.RAHI\Documents\Documents\Code\dahu-2'
# Path to the root of this Python project.


class BackupsToKeep(IntEnum):
    LAST_N_HOURS = 8
    LAST_N_DAYS = 7
    LAST_N_WEEKS = 6
    LAST_N_MONTHS = 5
    LAST_N_YEARS = 1

BACKUP_INTERVAL = timedelta(hours=1)
