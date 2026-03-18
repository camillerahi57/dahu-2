from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Self

import streamlit as st

from logic.constants import PAGE_NAME_KEY


@dataclass
class FormField[T](ABC):  # Generic type T.
    value: T
    id_: str
    is_valid: bool = False
    error_msg: str = ''
    has_changed: bool = False

    # def __init__(self, field_name: str = ''):
    #     """We can give the field a name in case two fields of the same type are on the
    #     same page. Otherwise, both fields would always have the same value."""
    #
    #     # If the field already exists in the current session:
    #     sess = st.session_state
    #     key = sess[PAGE_NAME_KEY] + self.__class__.__name__ + field_name
    #     if key in sess:
    #         self.__dict__ = sess[key].__dict__.copy()
    #
    #     # If first time loading the page:
    #     else:
    #         self.value: T
    #         # self.value = self._streamlit_input()
    #         self.is_valid: bool = False
    #         self.error_msg: str = ''
    #         self.has_changed: bool = False
    #         sess[key] = self  # Put it in current session.
    #
    #     # In both cases:
    #     self.value = self._streamlit_input()
    #     self.show_error()
    #     st.write(self.has_changed)
    #     st.write(self.error_msg)

    @property
    @abstractmethod
    def default_value(self) -> T:
        """Abstract property (a property that has to be set in subclass)."""
        pass

    @abstractmethod
    def _is_valid(self) -> tuple[bool, str]:
        """Is valid with an error message."""
        pass

    def _validate(self):
        self.is_valid, self.error_msg = self._is_valid()

    def on_change(self):
        """MUST be called to trigger validation. Usually called by Streamlit, when passed
        to the 'on_change='argument of a Streamlit input field."""
        self.has_changed = True

    def show_error(self):
        self._validate()
        if self.error_msg and self.has_changed:
            st.warning(self.error_msg)

    @classmethod
    def get_or_create(cls, id_: str) -> Self:
        sess = st.session_state
        key = cls.get_key(id_=id_)
        if key not in sess:
            sess[key] = cls(value=cls.default_value, id_=id_)
        return sess[key]

    def remove_from_session(self):
        sess = st.session_state
        key = self.get_key(id_=self.id_)
        del sess[key]

    @classmethod
    def get_key(cls, id_: str):
        sess = st.session_state
        return sess[PAGE_NAME_KEY] + cls.__name__ + id_

    @classmethod
    def input(cls, id_: str = ''):
        """Add an id if multiple fields of the same type are on the same page.
        This helps to avoid two problems:
            - Two fields copying each other's value.
            - A temporary field (like in a popup) being loaded as the one from the previous popup.
        """
        field = cls.get_or_create(id_=id_)
        field.value = field._streamlit_input()
        field.show_error()
        return field

    @abstractmethod
    def _streamlit_input(self):
        pass