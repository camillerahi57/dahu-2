from abc import abstractmethod, ABC
from datetime import datetime
from enum import StrEnum
from typing import Any

import streamlit as st
from pint.registry import Unit

from logic.constants import SessionKeys as Sk
from logic.lab_modelization.db_models import UserUploadedFile
from logic.units import to_db_unit, from_db_unit, ur


class FieldType(StrEnum):
    MANDATORY = 'mandatory'
    ADVISED = 'advised'
    OPTIONAL = 'optional'


class Field(ABC):
    def __init__(self, key: str|int = 'default_key', *, form_default,
                 db_default=None):
        prefill = form_default if db_default is None else db_default
        self.prefill = prefill
        self._input: Any
        self.err_msg: str
        self.is_valid: bool

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
        return self._input not in {'', None}

    @abstractmethod
    def _streamlit_input(self, prefill, key: str):
        raise NotImplementedError

    @abstractmethod
    def _validate(self, input_) -> tuple[bool, str]:
        raise NotImplementedError

    @property
    @abstractmethod
    def type(self) -> FieldType:
        raise NotImplementedError

    @property
    def value(self) -> Any:
        """Returns the value if valid, else None."""
        if not self.is_valid or not self.is_filled:
            return None
        return self._input


class UnitField(Field):
    def __init__(self, key: str|int = 'default_key', *, form_default,
                 db_default=None):
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
        raise NotImplementedError

    ui_unit_alias: str = None

    @property
    def value(self) -> Any:
        raise RuntimeError("`value` for a field that has a unit is ambiguous.")

    @property
    def in_db_unit(self) -> float|None:
        """Returns value but with DB unit if not None,else None."""
        if super().value is None:
            return None
        elif isinstance(super().value, int) or isinstance(super().value, float):
            as_ui_unit = ur.Quantity(super().value, self.ui_unit)
            return to_db_unit(as_ui_unit)
        else:
            raise ValueError(f"Type {type(super().value)} cannot have a unit.")

    @property
    def in_ui_unit(self) -> float|None:
        """Returns value but with DB unit if not None,else None."""
        return super().value

    @classmethod
    def to_ui_unit(cls, from_db: float|None) -> tuple[float|None, str|None]:
        if from_db is None:
            return None, None
        ui_quantity = from_db_unit(from_db, cls.ui_unit)  # noqa Wrong warning.
        if cls.ui_unit_alias:
            unit_str = cls.ui_unit_alias
        else:
            unit_str = f'{cls.ui_unit:~P}'

        return ui_quantity.magnitude, unit_str

    @classmethod
    def db_to_ui_str(cls, from_db: float) -> str:
        ui_value, unit_str = cls.to_ui_unit(from_db)
        return f'{ui_value:.3g} {unit_str}'


class Form(ABC):
    def __init__(self, fields: list[Field], sub_forms: list[Form],
                 *args, **kwargs):
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
        raise NotImplementedError


class FileUploadField(Field):
    type = FieldType.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        return st.file_uploader('Select a file', key=key, max_upload_size=2**16)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ is None:
            return False, 'Please upload a file.'
        return True, ''


class FileUploadForm(Form):
    def __init__(self, default_file: UserUploadedFile|None,
                 key: str = 'default_key',
                 accepted_formats: list[str] | None = None):
        from components.general import sess
        upload_fld = None

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
                        st.rerun()

            else:
                upload_fld = FileUploadField(key=key, form_default=None)
                if upload_fld.value:
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
        if self.accepted_formats is not None and self.original_file_name:
            extension = self.original_file_name.split('.')[-1].lower()
            accepted_formats = [f.lower() for f in self.accepted_formats]
            if extension not in accepted_formats:
                return False, (f'File extension {extension} not supported. '
                               f'Supported formats: {accepted_formats}.')
        return True, ''


class FileLabelField(Field):
    type = FieldType.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        return st.text_input("File Label", value=prefill, max_chars=50, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''



class PausePageRun(Exception):
    pass