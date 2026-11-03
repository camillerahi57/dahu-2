"""Building blocks shared by every form of the app.

A form page is made of *fields* (one input widget each, see `Field`)
grouped into *forms* (see `Form`), which can contain sub-forms. Each
field validates its own input as soon as it is drawn; each form then
combines the validity of its fields and sub-forms and adds checks that
involve several fields at once. The page enables its "Submit" button
only when the outermost form is valid.

Vocabulary:
    - An *abstract base class* (`ABC`) is a class that is not meant to
      be used directly, only subclassed. Its *abstract methods*
      (`@abstractmethod`) must be written by every subclass; Python
      refuses to create an object of a class that hasn't done so.
    - A *widget key* is the name Streamlit uses to recognize the same
      widget from one run of the page script to the next. Two widgets
      with the same key on one page make Streamlit raise an error.
    - A *rerun*: Streamlit runs the whole page script again, from the
      top, every time the user interacts with a widget.
    - The *session state* (`st.session_state`, here `sess`) is a
      dictionary that Streamlit keeps for each browser tab across
      reruns. It is how values survive from one run to the next.
"""

from abc import abstractmethod, ABC
from datetime import datetime
from enum import StrEnum
from typing import Any

import streamlit as st
from pint.registry import Unit

from dahu_2_config import MAX_UPLOAD_SIZE_MB
from logic.constants import SessionKeys as Sk
from logic.lab_modelization.db_models import UserUploadedFile
from logic.units import from_db_unit, ur, to_db_magnitude


class FieldType(StrEnum):
    """How much a field needs to be filled in.

    Attributes:
        MANDATORY: An empty field makes the field (and so the form)
            invalid, with the message "Mandatory field.".
        ADVISED: May be left empty. Currently handled exactly like
            OPTIONAL by `Field.__init__`.
        OPTIONAL: May be left empty.
    """

    MANDATORY = 'mandatory'
    ADVISED = 'advised'
    OPTIONAL = 'optional'


class Field(ABC):
    """One input widget of a form, which validates its own input.

    Creating the object draws the widget on the page, reads what the
    user typed, validates it and shows a warning under the widget if it
    is invalid. Everything happens in `__init__`, so a field must be
    created at the place on the page where it should appear.

    Subclasses must provide `_streamlit_input`, `_validate` and `type`
    (usually as a plain class attribute, e.g.
    `type = FieldType.MANDATORY`).

    Attributes:
        prefill: The value shown in the widget when it first appears:
            `db_default` if given, else `form_default`.
        is_valid: True if the input passed validation, or if the field
            is empty and not mandatory.
        err_msg: The warning shown under the widget; `''` if none.
    """

    def __init__(self, key: str|int = 'default_key', *, form_default,
                 db_default=None):
        """Draw the widget, read its input and validate it.

        Args:
            key: Makes the widget key unique. The widget key is
                `<class name in lower case>_<key>`, so `key` only needs
                to be distinct between fields of the same class on one
                page.
            form_default: Value to prefill on a "new" page.
            db_default: Value from an existing DB object, used on edit
                pages. When not None, it overrides `form_default`.
        """
        prefill = form_default if db_default is None else db_default
        self.prefill = prefill
        # Declared here (annotation only) so the IDE knows the
        # attributes; they are set below.
        self._input: Any
        self.err_msg: str
        self.is_valid: bool

        # `width='content'` keeps the warning below as narrow as the
        # widget instead of spanning the whole page.
        with st.container(width='content'):
            key = self.__class__.__name__.lower() + f'_{key}'
            self._input = self._streamlit_input(prefill, key)
            if self.is_filled:
                is_valid, err_msg = self._validate(self._input)
            else:
                if self.type == FieldType.MANDATORY:
                    is_valid, err_msg = False, 'Mandatory field.'
                elif self.type == FieldType.ADVISED:
                    is_valid, err_msg = True, ''
                else:
                    is_valid, err_msg = True, ''

            self.is_valid, self.err_msg = is_valid, err_msg

            if err_msg != '':
                with st.container(width='content', gap='xxsmall'):
                    st.warning(err_msg)

    @property
    def is_filled(self) -> bool:
        """Whether the user entered something.

        Only `''` and None count as empty: `0` and `False` are filled.

        Returns:
            True if the raw input is neither `''` nor None.
        """
        return self._input not in {'', None}

    @abstractmethod
    def _streamlit_input(self, prefill, key: str):
        """Draw the Streamlit widget and return what it holds.

        Called once by `Field.__init__`, on every rerun.

        Args:
            prefill: Value to show in the widget at first.
            key: Widget key to pass to the Streamlit widget. Some
                subclasses don't pass it, and Streamlit then builds a
                key from the widget's label and parameters.

        Returns:
            The widget's current value (the raw input).
        """
        raise NotImplementedError

    @abstractmethod
    def _validate(self, input_) -> tuple[bool, str]:
        """Check the raw input.

        Only called when the field is filled (see `is_filled`), so it
        doesn't need to handle `''` or None, unless the widget can
        return them in other cases.

        Args:
            input_: What `_streamlit_input` returned.

        Returns:
            `(is_valid, error message)`; the message is `''` when
            valid.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def type(self) -> FieldType:
        """Whether the field is mandatory, advised or optional.

        Returns:
            The field's `FieldType`.
        """
        raise NotImplementedError

    @property
    def value(self) -> Any:
        """The validated input.

        Returns:
            The raw input if the field is filled and valid, else None.
        """
        if not self.is_valid or not self.is_filled:
            return None
        return self._input


class UnitField(Field):
    """A field for a physical quantity, entered in a UI unit.

    The user types a number in `ui_unit` (e.g. µm), while the DB stores
    SI base units (e.g. m); see `logic/units.py`. This class does the
    conversion both ways, so a subclass only declares `ui_unit` once.

    Read the input with `in_db_unit` (or `in_ui_unit`); `value` raises
    an error so that nobody gets a number without knowing its unit.

    Attributes:
        ui_unit_alias: Text to show instead of Pint's symbol for
            `ui_unit`, e.g. `'SCCM'` for gas flows. None to use Pint's
            symbol.
    """

    def __init__(self, key: str|int = 'default_key', *, form_default,
                 db_default=None):
        """Convert `db_default` to the UI unit, then build the field.

        Args:
            key: See `Field.__init__`.
            form_default: Prefill on a "new" page, already in
                `ui_unit`.
            db_default: Value from the DB, in SI base units. It is
                converted to `ui_unit` before being shown.
        """
        if db_default is not None:
            db_default = from_db_unit(
                db_default, target_unit=self.ui_unit).magnitude
        super().__init__(
            key=key,
            form_default=form_default,
            db_default=db_default,
        )

    @property
    @abstractmethod
    def ui_unit(self) -> Unit:
        """The unit the user types the value in.

        Subclasses set it as a class attribute, e.g. `ui_unit = ur.um`.
        Changing it changes the unit everywhere in the app.

        Returns:
            A Pint unit.
        """
        raise NotImplementedError

    ui_unit_alias: str|None = None

    @property
    def value(self) -> Any:
        """Not available for unit fields: use `in_db_unit`.

        Raises:
            RuntimeError: Always.
        """
        raise RuntimeError("`value` for a field that has a unit is ambiguous.")

    @property
    def in_db_unit(self) -> float|None:
        """The validated input converted to SI base units.

        Returns:
            The magnitude in SI base units, or None if the field is
            empty or invalid.

        Raises:
            ValueError: If the widget returned something that is not a
                number.
        """
        if super().value is None:
            return None
        elif isinstance(super().value, int) or isinstance(super().value, float):
            as_ui_unit = ur.Quantity(super().value, self.ui_unit)
            return to_db_magnitude(as_ui_unit)
        else:
            raise ValueError(f"Type {type(super().value)} cannot have a unit.")

    @property
    def in_ui_unit(self) -> float|None:
        """The validated input as typed, in `ui_unit`.

        Returns:
            The magnitude in `ui_unit` (no conversion), or None if the
            field is empty or invalid.
        """
        # This docstring used to say "with DB unit", which was wrong.
        return super().value

    @classmethod
    def to_ui_unit(cls, from_db: float|None) -> tuple[float|None, str|None]:
        """Convert a DB value to this field's UI unit, for display.

        Args:
            from_db: Magnitude in SI base units, or None.

        Returns:
            `(magnitude in ui_unit, unit text)`. The unit text is
            `ui_unit_alias` if set, else Pint's short symbol. `(None,
            None)` if `from_db` is None.
        """
        if from_db is None:
            return None, None
        ui_quantity = from_db_unit(from_db, cls.ui_unit)  # noqa Wrong warning.
        if cls.ui_unit_alias:
            unit_str = cls.ui_unit_alias
        else:
            # `~P`: Pint's short ("~") and "pretty" (P) format, e.g. µm.
            unit_str = f'{cls.ui_unit:~P}'

        return ui_quantity.magnitude, unit_str

    @classmethod
    def db_to_ui_str(cls, from_db: float) -> str:
        """Format a DB value as text in the UI unit, e.g. `'1.5 µm'`.

        Args:
            from_db: Magnitude in SI base units.

        Returns:
            The value with 3 significant digits, a space and the unit.
        """
        ui_value, unit_str = cls.to_ui_unit(from_db)
        return f'{ui_value:.3g} {unit_str}'


class Form(ABC):
    """A group of fields and sub-forms that is valid as a whole.

    A subclass creates its fields and sub-forms in its own `__init__`
    (which draws them), stores the values it needs, and then must call
    `super().__init__(fields, sub_forms)`. Without that call,
    `is_valid` is never set and validation silently stops working.

    Attributes:
        fields: The fields passed in, without the Nones.
        sub_forms: The sub-forms passed in, without the Nones.
        all_flds_valid: True if every field is valid.
        all_sub_forms_valid: True if every sub-form is valid.
        is_coherent: Result of `_is_coherent`; True when it wasn't
            run.
        coherence_err: Message from `_is_coherent`; `''` if none.
        is_valid: True if all fields and sub-forms are valid and the
            form is coherent.
    """

    def __init__(self, fields: list[Field|None], sub_forms: list[Form|None],
                 *args, **kwargs):
        """Combine the validity of the fields and sub-forms.

        Runs `_is_coherent` only once every field and sub-form is
        valid, and shows a warning if it fails.

        Args:
            fields: Fields of this form. None entries are allowed (for
                fields that were not drawn) and ignored.
            sub_forms: Sub-forms of this form. None entries are
                ignored.
            *args: Ignored.
            **kwargs: Ignored.
        """
        fields = [f for f in fields if f is not None]  # Remove Nones.
        sub_forms = [s for s in sub_forms if s is not None]
        self.fields = fields
        self.sub_forms = sub_forms

        self.is_valid = False
        self.all_flds_valid = all(f.is_valid for f in fields)
        self.all_sub_forms_valid = all(form.is_valid for form in sub_forms)
        if self.all_flds_valid and self.all_sub_forms_valid:
            self.is_coherent, self.coherence_err = self._is_coherent()
        else:  # If not all fields are filled, we consider the values to be
            # coherent.
            self.is_coherent, self.coherence_err = True, ''

        if not self.is_coherent:
            with st.container(width='content'):
                st.warning(self.coherence_err)

        self.is_valid = all([
            self.all_flds_valid,
            self.all_sub_forms_valid,
            self.is_coherent
        ])

    @abstractmethod
    def _is_coherent(self) -> tuple[bool, str]:
        """Check rules that involve several fields or sub-forms.

        Called by `Form.__init__` only when every field and sub-form is
        valid, so the values the subclass stored can be trusted.

        Returns:
            `(is_coherent, error message)`; the message is `''` when
            coherent.
        """
        raise NotImplementedError


class FileUploadField(Field):
    """A file picker (`st.file_uploader`), used by `FileUploadForm`.

    Optional, and valid once a file is chosen. Its value is Streamlit's
    `UploadedFile` object. See `Field._validate`.
    """

    type = FieldType.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        """Draw a file picker; `prefill` is ignored.

        See `Field._streamlit_input`.
        """
        return st.file_uploader('Select a file', key=key,
                                max_upload_size=MAX_UPLOAD_SIZE_MB)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse a missing file. See `Field._validate`."""
        if input_ is None:
            return False, 'Please upload a file.'
        return True, ''


class FileUploadForm(Form):
    """Upload one file and give it a label.

    Shows a file picker. Once a file is chosen, its content is copied
    into the session state, the picker is replaced by the file name and
    a "Cancel" button, and a label field appears. On edit pages,
    `default_file` preloads an existing file the same way.

    The file is not saved by this form: the page builds the
    `UserUploadedFile` subclass from the attributes below and saves it.

    Side effects: writes the `SessionKeys` entries `UPLOADED_FILE`,
    `FILE_NAME`, `UPLOADED_AT` and `USE_DEFAULT_FILE`, each followed by
    `key`, and triggers reruns.

    Attributes:
        accepted_formats: Allowed file extensions, or None for any.
        original_file_name: Name of the file on the user's computer;
            None if no file.
        file_provided: True if a file name is stored.
        label: The label typed by the user; `''` if no file, None if
            the label field is empty.
        file_bytes: Content of the file; None if no file.
        upload_date: When the file was chosen, or the `upload_date` of
            `default_file`; None if no file.
    """

    def __init__(self, default_file: UserUploadedFile|None,
                 key: str = 'default_key',
                 accepted_formats: list[str] | None = None):
        """Draw the upload widgets and read the stored file.

        Args:
            default_file: Existing file to preload (edit pages), or
                None.
            key: Suffix of the session state keys and widget keys.
                Must differ between upload forms on the same page.
            accepted_formats: Allowed extensions without the dot, any
                case, e.g. `['png', 'jpg']`. Checked in
                `_is_coherent`, not by the file picker.
        """
        from logic.global_variables import sess
        upload_fld = None

        # The default file is preloaded on every run until the user
        # cancels it; afterwards it must not come back.
        if Sk.USE_DEFAULT_FILE+key not in sess:
            sess[Sk.USE_DEFAULT_FILE+key] = True

        if default_file and sess[Sk.USE_DEFAULT_FILE+key]:
            file_bytes = default_file.file_bytes
            sess[Sk.UPLOADED_FILE+key] = file_bytes
            sess[Sk.FILE_NAME+key] = default_file.original_file_name
            sess[Sk.UPLOADED_AT+key] = default_file.upload_date

        with st.container(horizontal=True):
            if Sk.UPLOADED_FILE+key in sess:
                with st.container(border=True, width='content',
                                  horizontal=True):
                    st.write(sess[Sk.FILE_NAME+key])
                    if st.button('🗑️ Cancel', key=key):
                        del sess[Sk.UPLOADED_FILE+key]
                        sess[Sk.USE_DEFAULT_FILE+key] = False
                        # Rerun so the file picker replaces the name.
                        st.rerun()

                        # TODO the "Cancel" button
                        #   deletes `UPLOADED_FILE` but not `FILE_NAME` or `UPLOADED_AT`, so
                        #   after cancelling, `original_file_name` and `file_provided` still
                        #   describe the cancelled file.

            else:
                upload_fld = FileUploadField(key=key, form_default=None)
                if upload_fld.value:
                    # The bytes are copied to the session state because
                    # the file picker disappears on the next run, and
                    # its file with it.
                    sess[Sk.UPLOADED_FILE+key] = upload_fld.value.read()
                    sess[Sk.FILE_NAME+key] = upload_fld.value.name
                    sess[Sk.UPLOADED_AT+key] = datetime.now()
                    st.rerun()

            if Sk.UPLOADED_FILE+key in sess:
                label_fld = FileLabelField(
                    key=key,
                    form_default='',
                    db_default=default_file.label if default_file else None,
                )
            else:
                label_fld = None

        self.accepted_formats = accepted_formats
        self.original_file_name = sess.get(Sk.FILE_NAME + key)
        self.file_provided = bool(self.original_file_name)
        self.label = label_fld.value if label_fld else ''
        self.file_bytes = sess.get(Sk.UPLOADED_FILE+key)
        self.upload_date = sess.get(Sk.UPLOADED_AT+key)
        super().__init__(fields=[upload_fld, label_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        """Refuse a file whose extension is not in `accepted_formats`.

        Pages subclass this form to add checks (e.g. a label already
        taken) and call this version at the end. See
        `Form._is_coherent`.
        """
        if self.accepted_formats is not None and self.original_file_name:
            extension = self.original_file_name.split('.')[-1].lower()
            accepted_formats = [f.lower() for f in self.accepted_formats]
            if extension not in accepted_formats:
                return False, (f'File extension {extension} not supported. '
                               f'Supported formats: {accepted_formats}.')
        return True, ''


class FileLabelField(Field):
    """Mandatory text input for the label of an uploaded file.

    At most 50 characters; any text is accepted. See `Field._validate`.
    """

    type = FieldType.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw a text input. See `Field._streamlit_input`."""
        return st.text_input("File Label", value=prefill, max_chars=50, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any label. See `Field._validate`."""
        return True, ''



class PausePageRun(Exception):
    """Raised to stop drawing the rest of a page.

    Forms raise it when the following part of the page makes no sense
    yet, e.g. while a step is unfinished. Every page wraps its body in
    `try: ... except PausePageRun: pass`, so the page simply ends there
    without an error.
    """

    pass
