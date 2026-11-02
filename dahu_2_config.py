"""Settings of Dahu DB that you may need to edit by hand.

Two blocks of settings exist: one for the production PC and one for
development. `ON_PRODUCTION` (set by the Windows environment variable
`dahu_db_production_mode`, see `logic.global_variables`) selects which
one is used.

Settings that have a second copy in `.streamlit/config.toml` (the port
and the maximum upload size) must be changed in both files.

Importing this module has no side effect besides reading the
environment variable.
"""

from datetime import timedelta
from enum import IntEnum

from logic.global_variables import ON_PRODUCTION

# Version of the code. It is stored in the database (`AppMetadata`) each
# time the metadata row is saved, so one can tell which version last wrote
# to a given database. Bump it at each release.
APP_VERSION: int = 10  # Must be an int.




if ON_PRODUCTION:
    DOMAIN = 'dahu-db.neel.cnrs.fr:80'  # URL of the DAHU DB app on Neel's
    # network (IP address with port number). Port is also in the file
    # ".streamlit/config.toml".
    # (Here it is a host name followed by the port, not an IP address.
    # It is the beginning of every link the app builds to its own pages.)

    RESTIC_PASSWORD = 'no_password'  # Password of the Restic repository,
    # probably 'no_password' as suggested in the Dahu DB setup manual.

    RESTIC_REPO_PATH = r'O:\DAHU2\dev\backups\restic_snapshot_repo'
    # Path to the Restic repository (on the server where the backups
    # are stored).
    # TODO The production `RESTIC_REPO_PATH` contains a `dev`
    #   folder (`O:\DAHU2\dev\backups\...`). Is that really the production
    #   repository?

    DAHU_2_CODE_BASE_PATH = r'C:\Users\camille.rahi\Documents\dahu-2'
    # Path to the root of this Python project.

else:
    # Development settings. The names mean the same as above. The Restic
    # repository must be a copy, so that development never touches the
    # production backups.
    DOMAIN = 'localhost:80'
    RESTIC_PASSWORD = 'no_password'
    RESTIC_REPO_PATH = (r'C:\Users\Camille.RAHI\Documents\Documents\Code'
                        r'\dev_restic_repo')
    DAHU_2_CODE_BASE_PATH = (r'C:\Users\Camille.RAHI\Documents\Documents\Code'
                             r'\dahu-2')


class BackupsToKeep(IntEnum):
    """How many Restic snapshots (backups) are kept, by time scale.

    An enumeration (enum) is a fixed list of named constants; here each
    constant is also an integer. Restic keeps the most recent snapshot
    of each of the last N hours, days, weeks, months and years, and
    forgets the others (see `logic.app_restoration`, which passes these
    numbers to the `restic forget --keep-*` options).
    """
    # Names say what the number counts, e.g. 8 = "keep the last 8 hours".
    LAST_N_HOURS = 8
    LAST_N_DAYS = 7
    LAST_N_WEEKS = 6
    LAST_N_MONTHS = 5
    LAST_N_YEARS = 1

# Minimum time between two automatic backups. A backup is only started
# when a page is loaded after this delay has passed, so the real delay
# can be longer if nobody uses the app.
BACKUP_INTERVAL = timedelta(hours=1)
# If the newest backup is older than this, the integrity check logs a
# "no recent backup" warning.
NO_RECENT_BACKUP_WARNING_TIMEDELTA = timedelta(days=7)

# Minimum time between two runs of the problem check (unknown enum
# values, missing files, old backup). Like backups, it only runs when a
# page is loaded.
PROBLEM_CHECK_INTERVAL = timedelta(hours=1, minutes=24)
# Whether the home page shows the banner listing detected problems.
SHOW_PROBLEM_BANNER = True
# Maximum size of an uploaded file, in megabytes (2**16 MB = 64 GB, so
# effectively unlimited).
MAX_UPLOAD_SIZE_MB = 2**16  # Also in config.toml.
