from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Self, Any

import streamlit as st

from logic.constants import SessionKeys as Sk


@dataclass
class FormField(ABC):  # Generic type T.
    value: Any
    id_: str
    is_valid: bool = False
    error_msg: str = ''
    has_changed: bool = False

    # def __init__(self, field_name: str = ''):
    #     """We can give the field a name in case two form_fields of the same type are on the
    #     same page. Otherwise, both form_fields would always have the same value."""
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
    def default_value(self):  # TODO remove that?
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
        return sess[Sk.PAGE_FILE_NAME] + cls.__name__ + id_

    @classmethod
    def input(cls, id_: str = '') -> Self:
        """Add an id if multiple form_fields of the same type are on the same page.
        This helps to avoid two problems:
            - Two form_fields copying each other's value.
            - A temporary field (like in a popup) being loaded as the one from the previous popup.
        """
        field = cls.get_or_create(id_=id_)
        field.value = field._streamlit_input()
        field.show_error()
        return field

    @abstractmethod
    def _streamlit_input(self):
        pass

#
# class PopupForm(ABC):
#     @property
#     @abstractmethod
#     def popup_title(self) -> str:
#         pass
#
#     def __init__(self):
#         self.all_fields: list[FormField] = []
#         # st.dialog is a decorator, which means it takes a function as an argument
#         # and returns another function. Here, the decorator has a parameter, that's why there are two
#         # bracket pairs. The first call returns the decorator, and the second one applies it to the
#         # function:
#         dialog_function = st.dialog(self.popup_title)(self.content)
#         # We can then call the decorated function:
#         dialog_function()
#         assert len(self.all_fields) > 0, "Please fill self.all_fields during the content method."
#
#     @abstractmethod
#     def content(self):
#         """You must populate the self.all_fields list so the form_fields are validated and cleaned afterward."""
#         pass
#
#     def clean_fields_and_rerun(self):
#         for fld in self.all_fields:
#             fld.remove_from_session()  # To have a new one in the next pop-up.
#         st.rerun()


@dataclass
class PopupData(ABC):
    all_form_fields: list[FormField]

    def __post_init__(self):
        self._assert_valid()

    @classmethod
    @abstractmethod
    def form_to_session(cls):
        pass

    # def reset_form_and_rerun(self):
    #     for fld in self.all_form_fields:
    #         fld.remove_from_session()  # To have a new one in the next pop-up.
    #     st.rerun()

    def _assert_valid(self):
        assert all(fld.is_valid for fld in self.all_form_fields), "Some form_fields are not valid."

    def clear_and_add_to_session(self, session_key: str) -> None:
        for fld in self.all_form_fields:
            fld.remove_from_session()
        sess = st.session_state
        if session_key not in sess:
            sess[session_key] = []
        sess[session_key].append(self)
        st.rerun()
