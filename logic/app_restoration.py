import json
import os
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self

import streamlit as st

from dahu_2_config import (RESTIC_PASSWORD, RESTIC_REPO_PATH,
                           DAHU_2_CODE_BASE_PATH, BackupsToKeep,
                           BACKUP_INTERVAL)
from logic.constants import USER_DATA_PATH
from logic.lab_modelization.base_classes import Event
from logic.lab_modelization.db_enums import EventType, LogSeverity
from logic.lab_modelization.db_models import AppLog

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
            event = Event.from_restic_error(result.returncode)
            AppLog.save_new(event)
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
    def delete_all_snaps(cls):
        for snap in cls.list_available():
            snap.delete()

    @classmethod
    def backup(cls, prune_excessive_snaps: bool = True):
        available = cls._backup_lock.acquire(blocking=False)
        if not available:
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
                event = Event.from_restic_error(result.returncode)
                AppLog.save_new(event)

            if prune_excessive_snaps:
                delete_excessive_snapshots()

            from components.general import app_metadata
            app_metadata.next_backup_at = datetime.now() + BACKUP_INTERVAL
            app_metadata.save()

            msg = f"Backup performed at {datetime.now()}."
            event = Event(EventType.BACKUP_PERFORMED, notify=False,
                          severity=LogSeverity.INFO, description=msg)
            AppLog.save_new(event)

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
            event = Event.from_restic_error(result.returncode)
            AppLog.save_new(event)

    def restore(self):
        subtree_to_restore = user_files_abs_path
        subtree_to_restore = subtree_to_restore.as_posix().replace(':', '')
        command = ['restic',
                   'restore',
                   self.id + ':' + subtree_to_restore,
                   '--target', user_files_abs_path,
                   '--repo', RESTIC_REPO_PATH,
                   '--delete',
                   '--json']

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
            env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ},
        )

        progress_bar = st.progress(0, text="Restoring…")
        for line in process.stdout:
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            pct = data.get("percent_done", 0)
            progress_bar.progress(pct, text=f"Restoring… {pct * 100:.0f}%")

        process.wait()
        if process.returncode != 0:
            event = Event.from_restic_error(process.returncode)
            AppLog.save_new(event)

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
    start = datetime.now()
    result = subprocess.run(
        command, capture_output=True, text=True,
        env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ},
    )
    if result.returncode != 0:
        event = Event.from_restic_error(result.returncode)
        AppLog.save_new(event)

def test():
    pass
    # Snapshot.delete_all_snaps()
    # Snapshot.create(delete_old_snaps=False)
    # id_ = 'b095ebd1efa36e99169fa12536b9722ab9483467763d77fb00efa3fa61f2b15c'
    # snap = Snapshot.from_id(id_)
    # snap.restore(delete_subsequent_snaps=True)

    # for s in Snapshot.list_available():
    #     print(s)


test()