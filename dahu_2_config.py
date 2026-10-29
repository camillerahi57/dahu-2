from datetime import timedelta
from enum import IntEnum

from logic.global_variables import ON_PRODUCTION

APP_VERSION: int = 10  # Must be an int.




if ON_PRODUCTION:
    DOMAIN = 'dahu-db.neel.cnrs.fr:80'  # URL of the DAHU DB app on Neel's
    # network (IP address with port number). Port is also in the file
    # ".streamlit/config.toml".

    RESTIC_PASSWORD = 'no_password'  # Password of the Restic repository,
    # probably 'no_password' as suggested in the Dahu DB setup manual.

    RESTIC_REPO_PATH = r'O:\DAHU2\dev\backups\restic_snapshot_repo'
    # Path to the Restic repository (on the server where the backups
    # are stored).

    DAHU_2_CODE_BASE_PATH = r'C:\Users\camille.rahi\Documents\dahu-2'
    # Path to the root of this Python project.

else:
    DOMAIN = 'localhost:80'
    RESTIC_PASSWORD = 'no_password'
    RESTIC_REPO_PATH = (r'C:\Users\Camille.RAHI\Documents\Documents\Code'
                        r'\dev_restic_repo')
    DAHU_2_CODE_BASE_PATH = (r'C:\Users\Camille.RAHI\Documents\Documents\Code'
                             r'\dahu-2')


class BackupsToKeep(IntEnum):
    LAST_N_HOURS = 8
    LAST_N_DAYS = 7
    LAST_N_WEEKS = 6
    LAST_N_MONTHS = 5
    LAST_N_YEARS = 1

BACKUP_INTERVAL = timedelta(hours=1)
NO_RECENT_BACKUP_WARNING_TIMEDELTA = timedelta(days=7)

PROBLEM_CHECK_INTERVAL = timedelta(hours=1, minutes=24)
SHOW_PROBLEM_BANNER = True
MAX_UPLOAD_SIZE_MB = 2**16  # Also in config.toml.