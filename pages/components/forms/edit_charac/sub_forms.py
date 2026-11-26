"""Form of the edit characterization page.

`RootForm` is the "new characterization" form (`new_charac/sub_forms.py`)
prefilled from an existing `Charac`, with three differences: the type
and the film cannot be changed, the data file is optional (leave it
empty to keep the current one), and the file's label can be edited.
"""
from datetime import date

import streamlit as st

from components.forms.base_classes import FileLabelField, Form
from components.forms.new_charac.sub_forms import (
    CHARAC_TYPES, CharacBaseInfoForm)
from logic.lab_modelization.base_classes import _BaseModel  # noqa Private
from logic.lab_modelization.db_models import (
    Charac, CharacFile, CharacReference)


class RootForm(Form):
    """The whole edit characterization form.

    Attributes:
        charac: The unsaved `Charac` that holds the edited values, with
            the id of the old one (so `save()` updates that row). Its
            `file` is the old file, or `new_file` if the file is
            replaced. None until the form is valid.
        file_label: The new label of the data file. None until the form
            is valid.
        new_file: The unsaved `CharacFile` of the replacement file, or
            None if the current file is kept (or the form is not valid
            yet). Also set when the current file is missing from the
            server and a file is added.
        file_stream: The replacement file, as an open binary file to give
            to `new_file.save_stream()`. None when `new_file` is None.
        new_subtype_rows: The unsaved subtype rows (e.g. the `Edx` with
            its elements) read from the replacement file; they replace
            the old ones. Empty when `new_file` is None.
    """

    def __init__(self, old_charac: Charac):
        """Draw the fields, prefilled from the existing characterization.

        Args:
            old_charac: The characterization being edited.
        """
        film = old_charac.film
        spec = CHARAC_TYPES[old_charac.type_]
        st.header(film.label)
        st.header(f'Edit {spec.name} characterisation')
        base_info_form = CharacBaseInfoForm(film, old_charac)

        st.divider()
        data_form = spec.data_form(old_charac)
        label_fld = FileLabelField(
            form_default=None, db_default=old_charac.file.label)

        super().__init__(
            fields=[label_fld], sub_forms=[base_info_form, data_form])

        self.charac = None
        self.file_label = None
        self.new_file = None
        self.file_stream = None
        self.new_subtype_rows: list[_BaseModel] = []
        if self.is_valid:
            self.file_label = label_fld.value
            charac = base_info_form.to_charac(id_=old_charac.id)
            charac.file = old_charac.file
            if data_form.file_stream is not None:
                # The internal name doesn't use the label, which the user
                # types: it could hold characters that are not allowed in
                # a file name.
                name_base = f'{spec.name} data'
                new_file = CharacFile(
                    label=self.file_label,
                    internal_file_name=CharacFile.new_internal_file_name(
                        name_base, data_form.original_file_name),
                    original_file_name=data_form.original_file_name,
                    upload_date=date.today(),
                )
                charac.file = new_file
                data_form.attach_to(charac)
                self.new_file = new_file
                self.file_stream = data_form.file_stream
                # `dependent_objects` would also give the references,
                # read from the DB: they must not be saved again.
                self.new_subtype_rows = [
                    row for row in charac.dependent_objects()
                    if not isinstance(row, CharacReference)]
            self.charac = charac

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''
