from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Self, Any

import streamlit as st

from logic.constants import SessionKeys as Sk


@dataclass
class FormField(ABC):  # Generic type T.
    value: Any
    field_key: str
    input_key: str
    is_valid: bool = False
    error_msg: str = ''
    has_changed: bool = False

    # def __init__(self, field_name: str = ''): """We can give the field a
    # name in case two form_fields of the same type are on the same page.
    # Otherwise, both form_fields would always have the same value."""
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

    # @property
    # @abstractmethod
    # def default_value(self):  # TODO remove that?
    #     """Abstract property (a property that has to be set in subclass)."""
    #     pass

    @abstractmethod
    def _is_valid(self) -> tuple[bool, str]:
        """Is valid with an error message."""
        pass

    def _validate(self):
        self.is_valid, self.error_msg = self._is_valid()

    def on_change(self):
        """MUST be called to trigger validation. Usually called by Streamlit,
        when passed to the 'on_change='argument of a Streamlit input field."""
        self.has_changed = True

    def show_error(self):
        self._validate()
        if self.error_msg and self.has_changed:
            st.warning(self.error_msg)

    @classmethod
    def get_or_create(cls, field_key: str, input_key: str) -> Self:
        sess = st.session_state
        if field_key not in sess:
            sess[field_key] = cls(value=None, field_key=field_key, 
                                   input_key=input_key)
        return sess[field_key]

    def remove_from_session(self):
        del st.session_state[self.field_key]

    @classmethod
    def get_field_key(cls, input_key: str):
        sess = st.session_state
        return 'field_' + sess[Sk.PAGE_FILE_NAME] + cls.__name__ + input_key

    @classmethod
    def get_input_key(cls, input_key: str):
        sess = st.session_state
        return 'widget_' + sess[Sk.PAGE_FILE_NAME] + cls.__name__ + input_key

    @classmethod
    def input(cls, key: str = '') -> Self:
        """Add a key if multiple form_fields of the same type are on the same
        page. This helps to avoid two problems: - Two form_fields copying
        each other's value. - A temporary field (like in a popup) being
        loaded as the one from the previous popup.
        """
        input_key = cls.get_input_key(key)
        field_key = cls.get_field_key(key)
        field = cls.get_or_create(field_key=field_key, input_key=input_key)
        field.value = field._streamlit_input()
        field.show_error()
        return field

    @abstractmethod
    def _streamlit_input(self):
        pass


@dataclass
class DialogData(ABC):
    all_form_fields: list[FormField]

    def __post_init__(self):
        self._assert_valid()

    @classmethod
    @abstractmethod
    def form(cls):
        pass

    def _assert_valid(self):
        assert all(fld.is_valid for fld in
                   self.all_form_fields), "Some form_fields are not valid."

    def clear_all_fields(self):
        """So that next time the dialog opens, all fields are empty."""
        for fld in self.all_form_fields:
            fld.remove_from_session()

    def clear_and_add_to_session(self, session_key: str) -> None:
        self.clear_all_fields()
        sess = st.session_state
        if session_key not in sess:
            sess[session_key] = []
        sess[session_key].append(self)
        st.rerun()
