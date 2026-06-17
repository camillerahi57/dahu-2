from abc import abstractmethod, ABC
from enum import StrEnum
from typing import Any

import streamlit as st
from pint.registry import Unit

from logic.units import to_db_unit, from_db_unit


class FieldType(StrEnum):
    MANDATORY = 'mandatory'
    ADVISED = 'advised'
    OPTIONAL = 'optional'

# TODO In validation in subclasses, it's better to use arguments like input
#  and key, other than self._pint and self.key.

class Field(ABC):
    def __init__(self, key: str|int = 'default_key', *, form_default,
                 db_default=None):
        form_default = form_default if db_default is None else db_default
        self.default = form_default
        self._input: Any
        self.err_msg: str
        self.is_valid: bool

        with st.container(width='content'):
            self.key = self.__class__.__name__.lower() + f'_{key}'
            self._input = self._streamlit_input(form_default)
            if self.is_filled:
                is_valid, err_msg = self._validate()
            else:
                if self.type == FieldType.MANDATORY:
                    is_valid, err_msg = False, 'Mandatory field.'
                elif self.type == FieldType.ADVISED:
                    is_valid, err_msg = True, ''
                    # is_valid, err_msg = True, 'Advised field.'
                else:
                    is_valid, err_msg = True, ''

            self.is_valid, self.err_msg = is_valid, err_msg

            if err_msg != '':
                with st.container(width='content'):
                    st.warning(err_msg)

    @property
    def is_filled(self) -> bool:
        return self._input not in {'', None}

    @abstractmethod
    def _streamlit_input(self, prefill):
        raise NotImplementedError

    @abstractmethod
    def _validate(self) -> tuple[bool, str]:
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
            db_default = from_db_unit(db_default, target_unit=self.ui_unit)
        super().__init__(
            key=key,
            form_default=form_default,
            db_default=db_default,
        )

    @property
    @abstractmethod
    def ui_unit(self) -> Unit:
        raise NotImplementedError

    @property
    def in_db_unit(self) -> float|None:
        """Returns value but with DB unit if not None,else None."""
        if self.value is None:
            return None
        elif isinstance(self.value, int) or isinstance(self.value, float):
            return to_db_unit(self.value * self.ui_unit)
        else:
            raise ValueError(f"Type {type(self.value)} cannot have a unit.")


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


class StopPageLoad(Exception):
    pass