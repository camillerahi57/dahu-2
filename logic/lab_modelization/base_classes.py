"""Base classes of the data model: the database object, the parent of
every table (`_BaseModel`) and the `Event` log entries.

An ORM (object-relational mapper) lets us handle database rows as Python
objects. Ours is Peewee: each table is a class that inherits from
`_BaseModel`, each row is an instance and each column is an attribute.
The tables themselves are defined in `db_models.py`.
"""
import csv
import io
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, Enum
from typing import Any, final, Iterable, get_type_hints, TYPE_CHECKING
from zoneinfo import ZoneInfo

from peewee import SqliteDatabase, IntegerField
from playhouse.shortcuts import model_to_dict
from playhouse.signals import Model

from dahu_2_config import RESTIC_REPO_PATH
from logic.constants import DB_PATH, DAHU_2_TIMEZONE
from logic.lab_modelization.db_enums import EventType, LogSeverity

# The one database object shared by all models. A pragma is a SQLite
# setting; `foreign_keys` is off by default in SQLite, and turning it on
# makes the database refuse rows that point to a missing row.
db = SqliteDatabase(DB_PATH, pragmas={'foreign_keys': 1})


# Annotation for an attribute that holds the "parts" of an object, i.e.
# the rows whose foreign key points to it (a foreign key is a column that
# stores the id of a row of another table; the rows that point back to a
# given row are its "backref"). `T` is the model of those rows: a generic
# type is a type with a parameter, as in `DependentBackref[Layer]`. At
# runtime this is only a list; `_BaseModel` reads the annotation to find
# which attributes to save (see `_BaseModel.dependent_object_fld_names`).
type DependentBackref[T] = list[T]

if TYPE_CHECKING:
    from logic.lab_modelization.db_models import UserUploadedFile, AppLog


class _BaseModel(Model):
    """Parent of every table class of Dahu DB.

    It adds to Peewee's `Model`: saving a whole graph of objects at
    once, recursive deletion of parts, display of values in UI units,
    consistency checks, and optional logging of every write.

    Attributes:
        id: Primary key of the row (unique integer given by SQLite).
        title_db_value_input_fields: Not a column. List of
            `(title, db_value, FieldClass)` tuples describing what to show
            about one object (see `data_string`). `FieldClass` is the
            form field that knows the UI unit of `db_value`, or any other
            class when the value has no unit. None if the model does not
            support `data_string`.
        log_db_write: Not a column. If True in a subclass, every save and
            deletion of its rows writes an `AppLog` row.
    """
    id: IntegerField

    # A list of attributes with title, corresponding attribute and input field.
    title_db_value_input_fields: list[tuple[str, Any, type]]|None = None
    # Write a new log at save/deletion if set to True in subclass:
    log_db_write: bool = False

    class Meta:
        """Peewee settings inherited by every table.

        Attributes:
            database: The database all tables live in.
            legacy_table_names: False, so that table names are the class
                names in snake_case (`TriodeSputtering` becomes
                `triode_sputtering`).
        """
        database = db
        legacy_table_names = False

    def __str__(self):
        """Describes the row as one "- column: value" line per column.

        Foreign keys are expanded into the row they point to. Used in
        the text of the `AppLog` entries written for saves and deletions.

        Returns:
            The multi-line text.
        """
        str_ = ''
        for k, v in model_to_dict(self).items():
            str_ += f'- {k}: {v}\n'
        return str_

    @final
    def save_with_dependent(self, *args, **kwargs):
        """Saves the object, then all the objects that depend on it.

        An object A depends on an object B if A has a foreign key towards
        B with the parameter `on_delete='RESTRICT'` or
        `on_delete='CASCADE'`. If the parameter is `on_delete='SET NULL'`,
        which means the foreign key can point to nothing, A does not
        depend on B. In the code, the dependents of a model are the
        attributes annotated with `DependentBackref`.

        The parent is saved first (so it has an id), then each dependent
        is saved the same way, recursively. Call it inside
        `with db.atomic():` (a transaction: if one save fails, all the
        saves are cancelled). `@final` tells type checkers that
        subclasses must not override it.

        Args:
            *args: Given to `save` for this object only.
            **kwargs: Given to `save` for this object only. The
                dependents are saved with default arguments, so for
                example `force_insert=True` is not passed on to them.
        """

        self.save(*args, **kwargs)
        for obj in self.dependent_objects():
            obj.save_with_dependent()
            # TODO Add "*args, **kwargs"?

    @classmethod
    def get_model_kwargs(cls, kwargs: dict[str, Any]):
        """Keeps only the keyword arguments that are columns of the model.

        Lets an `__init__` with explicit keyword arguments give just its
        columns to Peewee: it is called with `locals()`, which also holds
        `self`, `args`, `kwargs`... that Peewee must not receive.

        Args:
            kwargs: Any dictionary, typically the `locals()` of an
                `__init__`.

        Returns:
            The entries of `kwargs` whose key is a column name of this
            model.
        """
        return {k: v for k, v in kwargs.items()
                if k in cls._meta.sorted_field_names}

    @classmethod
    def dependent_object_fld_names(cls) -> Iterable[str]:
        """Finds the attributes that hold the dependents of an object.

        It looks at the class annotations: the names annotated with
        `DependentBackref[...]` are the ones returned. This is a
        generator: a function that hands its results one at a time
        (with `yield`) instead of building a list.

        Returns:
            The attribute names, one by one.
        """
        for name, hint in get_type_hints(cls).items():
            try:
                if hint.__origin__ == DependentBackref:
                    yield name
            except AttributeError:
                pass

    def dependent_objects(self) -> list[_BaseModel]:
        """Gets all the objects that depend on this one, all kinds mixed.

        For an unsaved object built by a form, the attributes are the
        lists assigned by the form. For a row read from the database,
        they are Peewee queries, which this method runs.

        Returns:
            The dependents, one level only (not their own dependents).
        """
        objects = []
        for fld_name in self.dependent_object_fld_names():
            new_objects = self.__getattribute__(fld_name)
            objects += list(new_objects)
        return objects

    def data_string(self, separator='\n\n'):
        """Describes the object with its values in UI units.

        Built from `title_db_value_input_fields`: for each tuple, the
        DB value is converted to the UI unit by the field class (see
        `UnitField.db_to_ui_str`). Values that are None are shown as
        `_None_`. Values for which the field class has no
        `db_to_ui_str` (no unit) are shown as they are.

        The import of `UnitField` is done here and not at the top of
        the file because `components` imports this module (circular
        import).

        Args:
            separator: Text put between two items.

        Returns:
            Markdown text, one `**title:** value` item per tuple.

        Raises:
            RuntimeError: If `title_db_value_input_fields` is None.
        """
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
        # TODO An `AttributeError` raised
        #   inside that method is silently shown as a raw value.

    def delete_parts(self):
        """Deletes the parts of this object (abstract method).

        An abstract method is one that every subclass must provide; the
        version here only raises an error. Implementations delete the
        rows that belong to this object, usually by calling
        `delete_with_parts` on each of them. Called by
        `delete_with_parts`.

        Raises:
            NotImplementedError: Always, if the subclass has not
                overridden it.
        """
        raise NotImplementedError

    @classmethod
    def get_problems(cls) -> Iterable[Event]:
        """Looks for incoherent data in the table of this model.

        Here it only looks for unknown enum values. Subclasses extend it
        (for example, `UserUploadedFile` also looks for missing files).
        Called for every model by `logic.db_integrity.get_problems`.
        This is a generator (see `dependent_object_fld_names`).

        Returns:
            One `Event` per problem found. Nothing is written to
            `AppLog` here.
        """
        for event in cls.seek_unknown_enums():
            yield event

    @classmethod
    def enum_fields(cls) -> Iterable[tuple[str, type[StrEnum]]]:
        """Finds the columns whose annotation is an enum class.

        Only plain annotations such as `x: MyEnum` are found. Those like
        `x: MyEnum | None` are skipped (so their values are not checked).

        Returns:
            `(attribute name, enum class)` pairs, one by one.
        """
        for name, hint in get_type_hints(cls).items():
            try:
                if issubclass(hint, StrEnum):
                    yield name, hint
            except TypeError:
                pass

    @classmethod
    def seek_unknown_enums(cls) -> Iterable[Event]:
        """Looks for stored enum values that the code does not know.

        It reads every row of the table, once per enum column. This can
        happen when an enum value was renamed or deleted in the code
        without a data migration.

        Returns:
            One `Event` (see `Event.from_unknown_enum`) per bad value.
        """
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
        """Deletes the object together with its parts, recursively.

        Safe: only the parts are deleted (see `delete_parts`), not
        the other objects that point to this one; if some still do, the
        database refuses the deletion. Order: parts, then the row, then
        the files (see `delete_related_files`). Call it inside
        `with db.atomic():`.

        Args:
            *args: Given to `delete_instance`.
            **kwargs: Given to `delete_instance`.
        """
        self.delete_parts()
        self.delete_instance(*args, **kwargs)
        self.delete_related_files()

    def delete_related_files(self):
        """Deletes the uploaded files linked to this row.

        Does nothing here. Models that store files override it (see
        `UserUploadedFile`). Called by `delete_with_parts`.
        """
        pass

    def delete_instance(self, recursive: bool = False,
                        delete_nullable: bool = False,
                        *args, **kwargs):
        """Deletes the row, and logs it first if `log_db_write` is True.

        Overrides Peewee's method. The log entry (`AppLog` row) is
        written before the deletion and needs a live Streamlit session.

        Args:
            recursive: Peewee option: also delete the rows that point to
                this one.
            delete_nullable: Peewee option: with `recursive`, also delete
                the rows whose foreign key can be empty (instead of
                emptying it).
            *args: Given to Peewee's method.
            **kwargs: Given to Peewee's method.
        """
        from logic.lab_modelization.db_models import AppLog
        if self.log_db_write:
            event = Event.from_deleted_item(self)
            AppLog.save_new(event)
        super().delete_instance(recursive, delete_nullable, *args, **kwargs)

    def save(self, force_insert: bool = False, only: list|None = None,
             *args, **kwargs):
        """Writes the row, and logs it first if `log_db_write` is True.

        Overrides Peewee's method. The log entry (`AppLog` row) is
        written before the save, so for a new row its text shows an
        empty id. It needs a live Streamlit session.

        Args:
            force_insert: Peewee option: always create a new row, even if
                the object has an id.
            only: Peewee option: the only columns to write.
            *args: Ignored.
            **kwargs: Ignored.
        """
        from logic.lab_modelization.db_models import AppLog
        if self.log_db_write:
            event = Event.from_saved_item(self)
            AppLog.save_new(event)
        super().save(force_insert, only)
        # TODO Add "*args, **kwargs"?

    @classmethod
    def all_rows_to_csv(cls, delimiter: str = ',') -> str:
        """Exports the whole table as CSV text.

        Values are as stored in the database (SI units, foreign keys as
        ids). Text is quoted and numbers are not.

        Args:
            delimiter: Character between two values of a line.

        Returns:
            The CSV text with a header line of column names, or an empty
            string if the table has no row.
        """
        row_dicts = cls.select().dicts()
        if not row_dicts:
            return ''

        output = io.StringIO()
        field_names = list(row_dicts[0].keys())
        writer = csv.DictWriter(
            output, fieldnames=field_names, quoting=csv.QUOTE_NONNUMERIC,  # noqa
            delimiter=delimiter)
        writer.writeheader()
        writer.writerows(row_dicts)  # noqa
        return output.getvalue()


@dataclass
class Event:
    """Something that happened in the app and may need to be logged.

    A dataclass is a class whose `__init__` is written automatically from
    its annotated attributes. An `Event` is stored by
    `AppLog.save_new`, which creates an `AppLog` row; those rows are
    shown on the logs page and, when `notify` is True, as a banner on the
    home page. Use the `from_...` constructors for the usual cases.

    Note that `AppLog.save` merges entries with the same description.

    Attributes:
        type: Kind of event (stored in `AppLog.event_type`).
        notify: True if users should be warned about it.
        severity: How serious it is.
        description: Human-readable text, which also identifies the
            event.
    """
    type: EventType
    notify: bool
    severity: LogSeverity
    description: str

    @classmethod
    def from_saved_item(cls, saved: _BaseModel):
        """Builds the event for the save of a row.

        Args:
            saved: The row being saved. Its text and the current time
                (local time of the PC) go in the description.

        Returns:
            An INFO event that does not notify.
        """
        return cls(
            type=EventType.SAVED_ITEM,
            notify=False,
            severity=LogSeverity.INFO,
            description=f"Saved {saved.__class__.__name__}. Value: {saved}. "
                        f"At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )

    @classmethod
    def from_deleted_item(cls, deleted: _BaseModel):
        """Builds the event for the deletion of a row.

        Args:
            deleted: The row being deleted. Its text and the current
                time (local time of the PC) go in the description.

        Returns:
            An INFO event that does not notify. Its type is
            `DELETED_ITEM`.
        """
        return cls(
            type=EventType.DELETED_ITEM,
            notify=False,
            severity=LogSeverity.INFO,
            # TODO Write Deleted instead of Saved:
            description=f"Saved {deleted.__class__.__name__}. Value: {deleted}"
                        f". At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )

    @classmethod
    def from_unknown_enum(cls, model_name: str, enum_class: type[Enum],
                          enum_val: Enum, field_name: str):
        """Builds the event for a stored value missing from its enum.

        Args:
            model_name: Name of the model class holding the value.
            enum_class: The enum the column is annotated with.
            enum_val: The unknown value, as read from the database (in
                practice a plain string).
            field_name: Name of the column.

        Returns:
            A CRITICAL event that notifies.
        """
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
        """Builds the event for a last backup that is too old.

        Asks Restic for the latest snapshot (see `Snapshot`), which runs
        the `restic` program. Called by `logic.db_integrity` once the
        age of that snapshot is over the limit set in the config.

        Returns:
            A CRITICAL event that notifies.
        """
        from logic.app_restoration import Snapshot

        # With timezone for difference between two tz-aware date-times:
        paris_now = datetime.now(tz=ZoneInfo(DAHU_2_TIMEZONE))
        last_backup_timedelta = paris_now - Snapshot.get_latest().time
        day_interval = last_backup_timedelta.days
        # TODO Wring snapshot id:
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
        """Builds the event for an uploaded file absent from the disk.

        Args:
            file: The row describing the file (its `internal_file_name`
                is the name looked for in the storage folder).

        Returns:
            A WARNING event that does not notify.
        """
        from logic.app_restoration import user_files_abs_path
        descr = (
            f"File \"{file.internal_file_name}\" for class "
            f"\"{file.__class__.__name__}\" "
            f"could not be found in Dahu DB's storage folder "
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
        """Builds the event for a failed call to the `restic` program.

        Restic is the backup tool (see `logic.app_restoration`).

        Args:
            error_code: Exit code of the `restic` process, the number
                it gives back to say whether it succeeded. 10 means that
                the repository (the backup folder) was not found.

        Returns:
            A CRITICAL event that notifies.
        """
        if error_code == 10:
            msg = (f"Restic repository not found. Dahu DB config file says it's"
                   f" supposed to be at location: \"{RESTIC_REPO_PATH}\".")
        else:
            msg = (f"Restic (tool for backup and restoration) error.\n\n"
                   f"Restic error code: {error_code} (Google it).")
        return cls(
            EventType.RESTIC_ERROR,
            notify=True,
            severity=LogSeverity.CRITICAL,
            description=msg,
        )
