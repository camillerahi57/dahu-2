"""Input fields specific to the new characterization form.

The date, author and comment fields are the ones of the film
modification form (`new_film_modif/fields.py`); this file only holds what
is specific to characterizations. See `Field` in
`components/forms/base_classes.py` for how fields draw and validate
themselves. They are assembled in `sub_forms.py`.
"""
import streamlit as st

from components.charac_info import modif_label
from components.forms.base_classes import Field, FieldType as Ft
from dahu_2_config import MAX_UPLOAD_SIZE_MB
from logic.lab_modelization.db_enums import CharacType
from logic.lab_modelization.db_models import FilmModification, Film

# Value of the `LastModifField` option "no modification yet". A real
# modification option holds the modification's id (never 0).
AS_DEPOSITED = 0


class CharacTypeField(Field):
    """Mandatory kind of characterization, a `CharacType` value.

    The choice decides which data form `RootForm` draws next. See
    `Field._validate`.

    Attributes:
        names: Display name of each selectable `CharacType`, in the
            order shown.
    """

    type = Ft.MANDATORY

    def __init__(self, key: str | int = 'default_key', *, form_default,
                 db_default=None, names: dict[CharacType, str]):
        """Store the selectable types, then draw the field.

        Args:
            key: See `Field.__init__`.
            form_default: See `Field.__init__`.
            db_default: See `Field.__init__`.
            names: The types the user can choose (only those that
                the app can handle yet) and their display names.
        """
        self.names = names  # Set before the widget is drawn.
        super().__init__(key=key, form_default=form_default,
                         db_default=db_default)

    def _streamlit_input(self, prefill, key: str):
        """Draw horizontal radio buttons, none selected at first.

        See `Field._streamlit_input`.
        """
        options = list(self.names)
        index = options.index(prefill) if prefill in options else None
        return st.radio('Characterisation type', options=options,
                        index=index, horizontal=True, key=key,
                        format_func=lambda type_: self.names[type_])

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any selectable type. See `Field._validate`."""
        return True, ''


class LastModifField(Field):
    """Mandatory choice of the last film modification before the
    measurement.

    The options are `AS_DEPOSITED` (the film had not been modified) and
    the id of each modification of the film. The user must choose, even
    if the date would allow guessing it: the form also checks that the
    choice agrees with the dates (see `CharacBaseInfoForm`). See
    `Field._validate`.

    Attributes:
        film: The measured film.
        modifs: Its modifications, in the order of the film's history.
    """

    type = Ft.MANDATORY

    def __init__(self, key: str | int = 'default_key', *, form_default,
                 db_default=None, film: Film):
        """Load the film's modifications, then draw the field.

        Args:
            key: See `Field.__init__`.
            form_default: See `Field.__init__`.
            db_default: See `Field.__init__`: `AS_DEPOSITED` or the id of
                a modification.
            film: The measured film.
        """
        self.film = film  # Set before the widget is drawn.
        self.modifs = film.ordered_modifs()
        super().__init__(key=key, form_default=form_default,
                         db_default=db_default)

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box of the film's history, none selected.

        See `Field._streamlit_input`.
        """
        labels = {AS_DEPOSITED: modif_label(None)}
        labels |= {modif.id: modif_label(modif) for modif in self.modifs}
        options = list(labels)
        index = options.index(prefill) if prefill in options else None
        return st.selectbox(
            'Last film modification before the measurement:',
            options=options, index=index, key=key, width=300,
            format_func=lambda id_: labels[id_])

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any option. See `Field._validate`."""
        return True, ''

    @property
    def selected_modif(self) -> FilmModification | None:
        """The chosen modification.

        Returns:
            The modification, or None if the film was measured as
            deposited, or if nothing is chosen yet.
        """
        if self.value in (None, AS_DEPOSITED):
            return None
        return next(m for m in self.modifs if m.id == self.value)


class CharacFileField(Field):
    """Mandatory file picker for the data file of a characterization.

    Its value is Streamlit's `UploadedFile` object. Unlike
    `FileUploadForm`, the file stays in the picker on reruns, so no
    session state is needed. See `Field._validate`.

    Attributes:
        label: Text shown above the picker.
        accepted_extensions: Allowed extensions, without the dot.
    """

    type = Ft.MANDATORY

    def __init__(self, key: str | int = 'default_key', *, form_default,
                 db_default=None, label: str, accepted_extensions: list[str]):
        """Store the picker settings, then draw the field.

        Args:
            key: See `Field.__init__`.
            form_default: See `Field.__init__`.
            db_default: See `Field.__init__`.
            label: Text shown above the picker.
            accepted_extensions: Extensions the picker accepts, without
                the dot, e.g. `['h5', 'hdf5']`.
        """
        self.label = label  # Set before the widget is drawn.
        self.accepted_extensions = accepted_extensions
        super().__init__(key=key, form_default=form_default,
                         db_default=db_default)

    def _streamlit_input(self, prefill, key: str):
        """Draw a file picker; `prefill` is ignored.

        See `Field._streamlit_input`.
        """
        return st.file_uploader(
            self.label, type=self.accepted_extensions, key=key,
            max_upload_size=MAX_UPLOAD_SIZE_MB)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any file the picker returns. See `Field._validate`."""
        return True, ''
