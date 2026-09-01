import csv
import io
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, Enum
from typing import Any, final, Iterable, get_type_hints, TYPE_CHECKING

from peewee import SqliteDatabase, IntegerField
from playhouse.shortcuts import model_to_dict
from playhouse.signals import Model

from logic.lab_modelization.db_enums import EventType, LogSeverity

db = SqliteDatabase('user_data/dahu_2.db', pragmas={'foreign_keys': 1})

type DependentBackref[T] = list[T]

if TYPE_CHECKING:
    from logic.lab_modelization.db_models import UserUploadedFile, AppLog


@dataclass
class Event:
    type: EventType
    notify: bool
    severity: LogSeverity
    description: str

    @classmethod
    def from_saved_item(cls, saved: _BaseModel):
        return cls(
            type=EventType.SAVED_ITEM,
            notify=False,
            severity=LogSeverity.INFO,
            description=f"Saved {saved.__class__.__name__}. Value: {saved}. "
                        f"At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )

    @classmethod
    def from_deleted_item(cls, deleted: _BaseModel):
        return cls(
            type=EventType.DELETED_ITEM,
            notify=False,
            severity=LogSeverity.INFO,
            description=f"Saved {deleted.__class__.__name__}. Value: {deleted}"
                        f". At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )

    @classmethod
    def from_unknown_enum(cls, model_name: str, enum_class: type[Enum],
                          enum_val: Enum, field_name: str):
        descr = (f"\"{enum_val}\" value for field \"{field_name}\" in "
                 f"model \"{model_name}\" is not a known value in "
                 f"\"{enum_class.__name__}\".")
        return cls(
            type=EventType.UNKNOWN_ENUM,
            notify=True,
            severity=LogSeverity.CRITICAL,
            description=descr,
        )

    @classmethod
    def from_no_recent_backup(cls):
        from logic.app_restoration import Snapshot
        last_backup_timedelta = datetime.now() - Snapshot.get_latest().time
        day_interval = last_backup_timedelta.days
        descr = (f'Last backup (snapshot id {Snapshot.id}) is very old '
                 f'(more than {day_interval} days ago).')
        return cls(
            type=EventType.NO_RECENT_BACKUP,
            notify=True,
            severity=LogSeverity.CRITICAL,
            description=descr,
        )

    @classmethod
    def from_file_missing(cls, file: UserUploadedFile):
        from logic.app_restoration import user_files_abs_path
        descr = (
            f"File \"{file.internal_file_name}\" for class "
            f"\"{file.__class__.__name__}\" "
            f"could not be found in Dahu 2's storage folder "
            f"\"{user_files_abs_path}\"."
        )
        return cls(
            type=EventType.FILE_MISSING,
            notify=False,
            severity=LogSeverity.WARNING,
            description=descr,
        )

    @classmethod
    def from_restic_error(cls, error_code: str|int):
        return cls(
            EventType.RESTIC_ERROR,
            notify=True,
            severity=LogSeverity.WARNING,
            description=f"Restic (tool for backup and restoration) error.\n\n"
                        f"Error code: {error_code}",
        )


class _BaseModel(Model):
    id: int | IntegerField

    # A list of attributes with title, corresponding attribute and input field.
    title_db_value_input_fields: list[tuple[str, Any, type]] = None
    # Write a new log at save/deletion if set to True in subclass:
    log_db_write: bool = False

    class Meta:
        database = db
        legacy_table_names = False

    def __str__(self):
        str_ = ''
        for k, v in model_to_dict(self).items():
            str_ += f'- {k}: {v}\n'
        return str_

    @final
    def save_with_dependent(self, *args, **kwargs):
        """Saves the object and all other objects that dependent on it.
        An object A depends on an object B if A has a foreign key towards B
        with de parameter [on_delete='RESTRICT'] or [on_delete='CASCADE'].
        If the parameter is [on_delete='SET NULL'], which means the foreign
        key can point to nothing, A does not dependent on B."""

        self.save(*args, **kwargs)
        for obj in self.dependent_objects():
            obj.save_with_dependent()

    @classmethod
    def get_model_kwargs(cls, kwargs: dict[str, Any]):
        """Gets a dictionary of keyword arguments, and returns a filtered
        version with only the ones that are needed to instantiate the model."""
        return {k: v for k, v in kwargs.items()
                if k in cls._meta.sorted_field_names}

    @classmethod
    def dependent_object_fld_names(cls) -> Iterable[str]:
        for name, hint in get_type_hints(cls).items():
            try:
                if hint.__origin__ == DependentBackref:
                    yield name
            except AttributeError:
                pass

    def dependent_objects(self) -> list[_BaseModel]:
        objects = []
        for fld_name in self.dependent_object_fld_names():
            new_objects = self.__getattribute__(fld_name)
            objects += list(new_objects)
        return objects

    def data_string(self, separator='\n\n'):
        from components.forms.base_classes import UnitField
        if self.title_db_value_input_fields is None:
            raise RuntimeError('self.title_db_value_input_fields is not set.')
        description_items = []
        for title, db_value, field in self.title_db_value_input_fields:
            try:
                field: UnitField
                quantity_str = field.db_to_ui_str(db_value) \
                    if db_value is not None else '_None_'
            except AttributeError:
                quantity_str = db_value if db_value is not None else '_None_'
            description_items.append(f"**{title}:** {quantity_str}")
        return separator.join(description_items)

    def delete_parts(self):
        raise NotImplementedError

    @classmethod
    def get_problems(cls) -> Iterable[Event]:
        for event in cls.seek_unknown_enums():
            yield event

    @classmethod
    def enum_fields(cls) -> Iterable[tuple[str, type[StrEnum]]]:
        for name, hint in get_type_hints(cls).items():
            try:
                if issubclass(hint, StrEnum):
                    yield name, hint
            except TypeError:
                pass

    @classmethod
    def seek_unknown_enums(cls) -> Iterable[Event]:
        for fld_name, enum_class in cls.enum_fields():
            for item in cls.select().dicts():
                if not item[fld_name] in enum_class:
                    yield Event.from_unknown_enum(
                        model_name=cls.__name__,
                        enum_class=enum_class,
                        enum_val=item[fld_name],
                        field_name=fld_name,
                    )

    def delete_with_parts(self, *args, **kwargs):
        """Recursive delete but safe (only deleting parts, not other dependent
        objects)."""
        self.delete_parts()
        self.delete_instance(*args, **kwargs)
        self.delete_related_files()

    def delete_related_files(self):
        pass

    def delete_instance(self, recursive: bool = False,
                        delete_nullable: bool = False,
                        *args, **kwargs):
        from logic.lab_modelization.db_models import AppLog
        if self.log_db_write:
            event = Event.from_deleted_item(self)
            AppLog.save_new(event)
        super().delete_instance(recursive, delete_nullable, *args, **kwargs)

    def save(self, force_insert: bool = False, only: list = None,
             *args, **kwargs):
        from logic.lab_modelization.db_models import AppLog
        if self.log_db_write:
            event = Event.from_saved_item(self)
            AppLog.save_new(event)
        super().save(force_insert, only, *args, **kwargs)

    @classmethod
    def all_rows_to_csv(cls, delimiter: str = ',') -> str:
        row_dicts = cls.select().dicts()
        if not row_dicts:
            return ''

        output = io.StringIO()
        field_names = list(row_dicts[0].keys())
        writer = csv.DictWriter(
            output, fieldnames=field_names, quoting=csv.QUOTE_NONNUMERIC,  # noqa
            delimiter=delimiter)
        writer.writeheader()
        writer.writerows(row_dicts)
        return output.getvalue()


