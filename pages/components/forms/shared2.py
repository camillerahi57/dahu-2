from abc import abstractmethod, ABC
from enum import StrEnum
from typing import Any, final

import streamlit as st


class FieldType(StrEnum):
    MANDATORY = 'mandatory'
    ADVISED = 'advised'
    OPTIONAL = 'optional'


class Field(ABC):
    @final
    def __init__(self, key: str|int = 'default_key', *, updated=None):
        with st.container(width='content'):
            self.is_updated = updated is not None
            self._input: Any
            self.err_msg: str
            self.is_valid: bool

            self.key = self.__class__.__name__.lower() + f'_{key}'
            self._input = self._streamlit_input(updated)
            if self.is_filled:
                is_valid, err_msg = self._validate()
            else:
                if self.type == FieldType.MANDATORY:
                    is_valid, err_msg = False, 'Mandatory field.'
                elif self.type == FieldType.ADVISED:
                    is_valid, err_msg = True, 'Advised field.'
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
    def _streamlit_input(self, updated=None):
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
        if not self.is_valid or not self.is_filled:
            return None
        return self._input


class Form(ABC):
    def __init__(self, fields: list[Field], sub_forms: list[Form],
                 *args, **kwargs):
        self.fields = fields
        self.sub_forms = sub_forms

        self.is_valid = False
        self.all_flds_valid = all(f.is_valid for f in fields)
        self.all_sub_forms_valid = all(form.is_valid for form in sub_forms)
        if self.all_flds_valid and self.all_sub_forms_valid:
            self.is_coherent, self.coherence_err = self._check_coherence()
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

    @classmethod
    @abstractmethod
    def _check_coherence(cls) -> tuple[bool, str]:
        raise NotImplementedError


class StopPageLoad(Exception):
    pass