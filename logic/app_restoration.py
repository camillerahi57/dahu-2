"""Backups and restores of the app state, through the Restic program.

Restic is a backup tool used from the command line; this module runs it
with `subprocess` (launching another program and reading its output).
Each Restic snapshot is a copy of the whole `user_data/` folder, the DB
file and the uploaded files together, so a restore brings back a
consistent "app state". The repository (where snapshots are stored) and
its password are set in `dahu_2_config.py`.

Every Restic failure writes a CRITICAL `AppLog` row.
"""
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

# Absolute path of `user_data/`, the folder that is backed up. Restic
# stores absolute paths, so the relative `USER_DATA_PATH` is not enough.
user_files_abs_path = Path(DAHU_2_CODE_BASE_PATH) / USER_DATA_PATH


@dataclass
class Snapshot:
    """One Restic snapshot, i.e. one saved copy of `user_data/`.

    A dataclass is a class whose `__init__` Python writes from the
    annotated attributes. Objects are built from `restic snapshots`
    output; creating one does not create a snapshot (use `backup`).

    Attributes:
        id: Restic's snapshot id (a 64-character hexadecimal string).
        time: When the snapshot was taken, timezone-aware.
        _backup_lock: Shared by all instances (no annotation, so not a
            dataclass field). A lock lets only one thread (a task
            running in parallel with the page) hold it at a time; here
            it prevents two simultaneous backups.
    """
    id: str
    time: datetime
    _backup_lock = threading.Lock()

    def __str__(self):
        """Returns the time and id, as shown on the admin page.

        Returns:
            E.g. `'2026-01-05 10:00:00+01:00        b095eb...'`.
        """
        return f"{self.time}        {self.id}"

    @classmethod
    def list_available(cls) -> list[Self]:
        """Lists the snapshots in the Restic repository.

        Side effects: shows a Streamlit spinner while Restic runs, and
        writes an `AppLog` row if it fails.

        Returns:
            The snapshots, in Restic's order, or an empty list if Restic
            failed.
        """
        with st.spinner("Listing available snapshots...", show_time=True):  # noqa
            result = subprocess.run(
                ["restic", "snapshots", "--json", "--repo", RESTIC_REPO_PATH],
                capture_output=True, text=True,
                env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ}
            )
        if result.returncode != 0:
            event = Event.from_restic_error(result.returncode)
            AppLog.save_new(event)
            return []
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
        """Returns the most recent snapshot.

        Returns:
            The snapshot with the latest `time`.

        Raises:
            IndexError: There is no snapshot, or Restic failed (not on
                purpose; see DOC_NOTES.md).
        """
        # TODO What if there are no snapshots?
        all_ = cls.list_available()
        return sorted(all_, key=lambda x: x.time)[-1]

    @classmethod
    def delete_all_snaps(cls):
        """Deletes every snapshot in the repository. Cannot be undone.

        Only called by `logic/migrations/table_creation.py`.

        Raises:
            RuntimeError: Restic failed to delete a snapshot.
        """
        for snap in cls.list_available():
            snap.delete()

    @classmethod
    def backup(cls, prune_excessive_snaps: bool = True):
        """Takes a new snapshot of `user_data/`.

        `init_page` runs it in a background thread once
        `AppMetadata.next_backup_at` has passed. If a backup is already
        running, returns at once without doing anything.

        On success: optionally deletes old snapshots
        (`delete_excessive_snapshots`), sets the next backup time to now
        + `BACKUP_INTERVAL`, saves `AppMetadata`, and writes an INFO
        `AppLog` row.

        Args:
            prune_excessive_snaps: Whether to then delete the snapshots
                not kept by the `BackupsToKeep` policy.

        Raises:
            RuntimeError: Restic failed (an `AppLog` row is written
                first).
        """
        print("Starting backup...")
        # Several page loads can start a backup thread before the first
        # one updates `next_backup_at`; non-blocking acquire lets the
        # extra threads give up instead of queueing.
        available = cls._backup_lock.acquire(blocking=False)
        if not available:
            print("Backup not available.")
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
                raise RuntimeError(result.stderr)
            # TODO runs in a background thread
            #   started by `init_page`, but `AppLog.save_new` reads `st.context` and
            #   cookies, which need the Streamlit script's own thread. Logging a
            #   backup (success or Restic error) may fail there.
            if prune_excessive_snaps:
                delete_excessive_snapshots()

            from logic.meta_data_init import app_metadata
            app_metadata.next_backup_at = datetime.now() + BACKUP_INTERVAL
            app_metadata.save()

            msg = f"Backup performed at {datetime.now()}."
            event = Event(EventType.BACKUP_PERFORMED, notify=False,
                          severity=LogSeverity.INFO, description=msg)
            AppLog.save_new(event)

        finally:
            Snapshot._backup_lock.release()
            print("Finished.")

    def delete_subsequent(self):
        """Deletes every snapshot taken after this one.

        Called after a restore, so the repository's history ends at the
        restored state.

        Raises:
            RuntimeError: Restic failed to delete a snapshot.
        """
        subsequent_snaps = [s for s in Snapshot.list_available()
                            if s.time > self.time]
        for s in subsequent_snaps:
            s.delete()

    def delete(self):
        """Deletes this snapshot from the repository and frees its space.

        `restic forget` removes the snapshot; `--prune` then deletes the
        stored data no other snapshot uses.

        Raises:
            RuntimeError: Restic failed (an `AppLog` row is written
                first).
        """
        command = ["restic", "forget", self.id, '--prune',
                   '--repo', RESTIC_REPO_PATH]
        result = subprocess.run(
            command, capture_output=True, text=True,
            env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ},
        )
        if result.returncode != 0:
            event = Event.from_restic_error(result.returncode)
            AppLog.save_new(event)
            raise RuntimeError(result.stderr)

    def restore(self):
        """Replaces `user_data/` (DB and files) with this snapshot.

        Called from the admin page. `--delete` removes files that are
        not in the snapshot. Shows a Streamlit progress bar. Then deletes
        every later snapshot, sets the next backup time to now +
        `BACKUP_INTERVAL` and saves `AppMetadata` (in the restored DB).

        Raises:
            RuntimeError: Restic failed (an `AppLog` row is written
                first).
        """
        subtree_to_restore = user_files_abs_path
        # TODO check that:
        # Inside a snapshot, Restic names a Windows path like
        # `C:/a/b` as `/C/a/b`: forward slashes and no colon.
        # `<id>:<subfolder>` restores only that subfolder, so its content
        # lands directly in `--target`.
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
        # With `--json`, Restic prints one JSON status object per line
        # while it works; `Popen` (unlike `run`) lets us read them live.
        for line in process.stdout:  # noqa
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
            raise RuntimeError(process.stderr)

        self.delete_subsequent()

        from logic.meta_data_init import app_metadata
        app_metadata.next_backup_at = datetime.now() + BACKUP_INTERVAL
        app_metadata.save()


def delete_excessive_snapshots():
    """Deletes the snapshots not kept by the `BackupsToKeep` policy.

    Keeps the last snapshot of each of the last N hours, days, weeks,
    months and years (N set in `dahu_2_config.py`), then frees the space.
    Called after each backup. On failure, writes an `AppLog` row but does
    not raise.
    """
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
    # start = datetime.now()
    result = subprocess.run(
        command, capture_output=True, text=True,
        env={"RESTIC_PASSWORD": RESTIC_PASSWORD, **os.environ},
    )
    if result.returncode != 0:
        event = Event.from_restic_error(result.returncode)
        AppLog.save_new(event)

def test():
    """Scratch function for manual tests. Currently does nothing.

    It is called at import time (below); the commented-out lines use
    method names that no longer exist (`create`, `from_id`).
    """
    pass
    # TODO Delete this function.
    # Snapshot.delete_all_snaps()
    # Snapshot.create(delete_old_snaps=False)
    # id_ = 'b095ebd1efa36e99169fa12536b9722ab9483467763d77fb00efa3fa61f2b15c'
    # snap = Snapshot.from_id(id_)
    # snap.restore(delete_subsequent_snaps=True)

    # for s in Snapshot.list_available():
    #     print(s)


test()