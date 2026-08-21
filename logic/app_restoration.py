import json
import os
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self

from dahu_2_config import (RESTIC_PASSWORD, RESTIC_REPO_PATH,
                           DAHU_2_CODE_BASE_PATH, BackupsToKeep,
                           BACKUP_INTERVAL)
from logic.constants import USER_DATA_PATH

user_files_abs_path = Path(DAHU_2_CODE_BASE_PATH) / USER_DATA_PATH


@dataclass
class Snapshot:
    id: str
    time: datetime
    _backup_lock = threading.Lock()

    def __str__(self):
        return f"{self.time}        {self.id}"

    @classmethod
    def list_available(cls) -> list[Self]:
        result = subprocess.run(
            ["restic", "snapshots", "--json", "--repo", RESTIC_REPO_PATH],
            capture_output=True, text=True,
            env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ}
        )
        if result.returncode != 0:
            raise RuntimeError(f"Database dump error: {result.stderr}")
        snap_dicts = json.loads(result.stdout)
        snap_list = [
            cls(
                id=d['id'],
                time=datetime.fromisoformat(d['time'])
            )
            for d in snap_dicts
        ]
        return snap_list

    @classmethod
    def get_latest(cls) -> Self:
        all_ = cls.list_available()
        return sorted(all_, key=lambda x: x.time)[-1]

    @classmethod
    def from_id(cls, id_: str) -> Self:
        for snap in Snapshot.list_available():
            if snap.id == id_:
                return snap
        raise RuntimeError(f"Snapshot not found: {id_}")

    @classmethod
    def delete_all_snaps(cls):
        for snap in cls.list_available():
            snap.delete()

    @classmethod
    def backup(cls, prune_excessive_snaps: bool = True):
        available = cls._backup_lock.acquire(blocking=False)
        if not available:
            print("Backup already in progress, skipping.")
            return  # Another thread is already backing up.

        try:
            command = ["restic", "backup", user_files_abs_path,
                       "--json", "--repo",
                       RESTIC_REPO_PATH]
            result = subprocess.run(
                command, capture_output=True, text=True,
                env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ}
            )
            if result.returncode != 0:
                raise RuntimeError(f"Database dump error: {result.stderr}")

            if prune_excessive_snaps:
                delete_excessive_snapshots()

            from components.general import app_metadata
            app_metadata.next_backup_at = datetime.now() + BACKUP_INTERVAL
            app_metadata.save()
        finally:
            Snapshot._backup_lock.release()

    def delete_subsequent(self):
        subsequent_snaps = [s for s in Snapshot.list_available()
                            if s.time > self.time]
        for s in subsequent_snaps:
            s.delete()

    def delete(self):
        command = ["restic", "forget", self.id, '--prune',
                   '--repo', RESTIC_REPO_PATH]
        result = subprocess.run(
            command, capture_output=True, text=True,
            env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ},
        )
        if result.returncode != 0:
            raise RuntimeError(f"Database dump error: {result.stderr}")

    def restore(self):
        subtree_to_restore = user_files_abs_path  # We don't restore the full
        # directory tree from Windows file system root (e.g. C:).
        # Make it Linux like:
        subtree_to_restore = subtree_to_restore.as_posix().replace(':', '')
        command = ['restic',
                   'restore',
                   self.id+':'+subtree_to_restore,
                   '--target', user_files_abs_path,
                   '--repo', RESTIC_REPO_PATH,
                   '--delete']  # --delete removes files that are not in
        # snapshot.
        result = subprocess.run(
            command, capture_output=True, text=True,
            env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ},
        )
        if result.returncode != 0:
            raise RuntimeError(f"Database dump error: {result.stderr}")

        self.delete_subsequent()

        from components.general import app_metadata
        app_metadata.next_backup_at = datetime.now() + BACKUP_INTERVAL
        app_metadata.save()


def delete_excessive_snapshots():
    command = [
        'restic',
        'forget',
        '--keep-hourly', str(BackupsToKeep.LAST_N_HOURS),
        '--keep-daily', str(BackupsToKeep.LAST_N_DAYS),
        '--keep-weekly', str(BackupsToKeep.LAST_N_WEEKS),
        '--keep-monthly', str(BackupsToKeep.LAST_N_MONTHS),
        '--keep-yearly', str(BackupsToKeep.LAST_N_YEARS),
        '--prune',
        '--repo', RESTIC_REPO_PATH,
    ]
    print("Starting forget-prune...")
    start = datetime.now()
    result = subprocess.run(
        command, capture_output=True, text=True,
        env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ},
    )
    print(f"Finished forget-prune ({datetime.now() - start})")
    if result.returncode != 0:
        raise RuntimeError(f"Database dump error: {result.stderr}")

def test():
    # Snapshot.delete_all_snaps()
    # Snapshot.create(delete_old_snaps=False)
    # id_ = 'b095ebd1efa36e99169fa12536b9722ab9483467763d77fb00efa3fa61f2b15c'
    # snap = Snapshot.from_id(id_)
    # snap.restore(delete_subsequent_snaps=True)

    for s in Snapshot.list_available():
        print(s)


test()