"""Forms of the new characterization page.

`RootForm` draws the information common to every characterization
(`CharacBaseInfoForm`), then the data form of the chosen type (`EdxForm`
for an EDX). Its `charac` and `charac_file` attributes are the unsaved
objects that `pages/new_charac.py` saves.

`CHARAC_TYPES` is the list of the kinds of characterization the app can
handle. **To add a new kind**, write a `CharacDataForm` subclass like
`EdxForm`, a drawing function like `components.charac_info.edx_info`,
and add one entry to `CHARAC_TYPES`; the library page and the new
charac page then use it without any other change. The subtype model and
its deletion are described in the docstring of `Charac`.
"""
from abc import abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, BinaryIO, Callable

import streamlit as st

from components.charac_info import edx_charac_info, edx_info, modif_label
from components.forms.base_classes import Form, PausePageRun
from components.forms.new_charac.fields import (
    CharacTypeField, LastModifField, CharacFileField)
from components.forms.new_film_modif.fields import (
    MadeOnField, MadeByField, CommentField)
from logic.constants import CookieKeys as Ck, SessionKeys as Sk
from logic.cookie_init import new_controller
from logic.global_variables import sess
from logic.lab_modelization.db_enums import CharacType
from logic.lab_modelization.db_models import Charac, CharacFile, Edx, Film


class CharacDataForm(Form):
    """What a characterization form needs from the form of one type.

    Subclasses draw the inputs of one `CharacType` (at least its data
    file), and say how to turn them into the type's subtype rows.

    Data files can be several GB. Streamlit keeps an uploaded file in
    memory; subclasses must read it as it is (never `getvalue()`, never
    copy it, never hash it), and must not read it again at every rerun
    (see `read_upload_once`).

    Attributes:
        file_stream: The data file as an open binary file (Streamlit's
            `UploadedFile`), or None if not given yet.
        original_file_name: Name of the data file on the user's
            computer, or None if not given yet.
    """

    file_stream: BinaryIO | None
    original_file_name: str | None

    @abstractmethod
    def attach_to(self, charac: Charac):
        """Create the subtype rows and attach them to the charac.

        Only called once the form is valid. The rows are unsaved: the
        page saves them with `charac.save_with_dependent()`.

        Args:
            charac: The unsaved characterization. Its subtype list (e.g.
                `edxs`) is set by this method.
        """
        raise NotImplementedError


def read_upload_once(
        uploaded: BinaryIO,
        read: Callable[[BinaryIO, Callable[[int, int], None]], Any],
) -> tuple[Any, str]:
    """Read an uploaded data file the first time only.

    Streamlit reruns the page script at every click, but the file is
    big and reading it is slow: the result is kept in the session state
    (see `SessionKeys.PARSED_UPLOAD`), identified by the upload's
    `file_id`, so it is only read again if the user picks another file.
    (`st.cache_data` is not an option: it would hash the whole file at
    every rerun.) A progress bar is shown while reading.

    Args:
        uploaded: Streamlit's `UploadedFile`.
        read: Reads the file: called as `read(uploaded, progress)`, where
            `progress(done, total)` moves the progress bar. Returns what
            has to be kept (small, plain Python values).

    Returns:
        `(result, error message)`. The result is None if reading failed,
        and the message is `''` if it worked.
    """
    kept = sess.get(Sk.PARSED_UPLOAD)
    if kept is not None and kept[0] == uploaded.file_id:
        return kept[1], kept[2]

    bar = st.progress(0, text=f'Reading {uploaded.name}...')

    def progress(done: int, total: int):
        """Move the progress bar to `done` out of `total`."""
        bar.progress(done / total if total else 1.0,
                     text=f'Reading {uploaded.name}: '
                          f'{done} / {total} positions')

    try:
        result, error = read(uploaded, progress), ''
    except Exception as e:  # noqa The file comes from the user and any
        # content can break the reading: show what went wrong instead of
        # crashing the page.
        result, error = None, f"{type(e).__name__}: {e}"
    bar.empty()
    sess[Sk.PARSED_UPLOAD] = (uploaded.file_id, result, error)
    return result, error


class EdxForm(CharacDataForm):
    """EDX data file (HDF5), read to fill the `Edx` rows.

    Shows the file picker, then a preview of what was read from the
    file. The form is invalid while the file is missing or unreadable;
    the reason is shown to the user.
    """

    def __init__(self):
        """Draw the file picker and read the file, if any."""
        st.subheader('EDX data')
        file_fld = CharacFileField(
            label='EDX data file (HDF5)',
            accepted_extensions=['h5', 'hdf5'],
            form_default=None,
        )

        self.file_stream = None
        self.original_file_name = None
        self._parsed = None
        self._parse_error = ''
        uploaded = file_fld.value
        if uploaded is not None:
            self.file_stream = uploaded
            self.original_file_name = uploaded.name
            self._parsed, error = read_upload_once(uploaded, Edx.read_hdf5)
            if error:
                self._parse_error = (
                    f"This file cannot be read as an EDX file ({error}).")

        if self._parsed is not None:
            with st.expander('Data read from the file', expanded=True):
                edx_info(Edx.from_parsed(None, self._parsed))  # noqa

        super().__init__(fields=[file_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        """Refuse a file that cannot be read. See `Form._is_coherent`."""
        if self._parse_error:
            return False, self._parse_error
        return True, ''

    def attach_to(self, charac: Charac):
        """Set `charac.edxs` to the `Edx` read from the file.

        See `CharacDataForm.attach_to`.
        """
        charac.edxs = [Edx.from_parsed(charac, self._parsed)]


@dataclass(frozen=True)
class CharacTypeSpec:
    """Everything the app needs to know about one kind of
    characterization.

    A dataclass is a class whose `__init__` is written automatically from
    its annotated attributes.

    Attributes:
        name: Display name, used on buttons and in titles.
        data_form: The form asking for the type's data file and the
            other inputs specific to the type.
        draw_info: Draws what the characterization holds, from the DB
            (for the library page).
    """
    name: str
    data_form: type[CharacDataForm]
    draw_info: Callable[[Charac], None]


# The kinds of characterization the app can handle. `CharacType` has more
# values (MOKE...), but they cannot be added until they have an entry here.
CHARAC_TYPES: dict[CharacType, CharacTypeSpec] = {
    CharacType.EDX: CharacTypeSpec(
        name='EDX', data_form=EdxForm, draw_info=edx_charac_info),
}


class CharacBaseInfoForm(Form):
    """Type, date, author, last film modification and comment of a
    characterization.

    Attributes:
        film: The measured film.
        charac_type: The chosen `CharacType`, or None.
        made_on: The date of the measurement, or None.
        made_by: The author's email address, or None.
        last_modif: The last modification before the measurement, or
            None (film measured as deposited, or nothing chosen yet).
        comment: The comment; `''` or None if empty.
    """

    def __init__(self, film: Film):
        """Draw the common fields.

        Reads the "last email used" cookie (a small value the browser
        stores for the app between visits) to prefill the author.

        Args:
            film: The measured film.
        """
        self.film = film
        type_fld = CharacTypeField(
            form_default=None,
            names={type_: spec.name for type_, spec in CHARAC_TYPES.items()},
        )
        with st.container(horizontal=True):
            made_on_fld = MadeOnField(form_default=None)
            made_by_fld = MadeByField(
                form_default=new_controller().get(Ck.LAST_EMAIL_USED))
        last_modif_fld = LastModifField(form_default=None, film=film)
        comment_fld = CommentField(form_default='')

        self.charac_type = type_fld.value
        self.made_on = made_on_fld.value
        self.made_by = made_by_fld.value
        self.last_modif = last_modif_fld.selected_modif
        self.comment = comment_fld.value
        # Only used by `_is_coherent`: the modification that follows
        # the chosen one in the film's history, if any.
        self._next_modif = None
        if last_modif_fld.value is not None:
            next_number = (0 if self.last_modif is None
                           else self.last_modif.modif_number + 1)
            self._next_modif = next(
                (m for m in last_modif_fld.modifs
                 if m.modif_number == next_number), None)

        super().__init__(
            fields=[type_fld, made_on_fld, made_by_fld, last_modif_fld,
                    comment_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """Check the dates against the chosen last modification.

        The measurement cannot be older than the modification chosen as
        the last one, and the modification that follows it must not be
        older than the measurement (the user would have forgotten it).
        Same-day dates are accepted, as the order within a day is
        unknown. See `Form._is_coherent`.
        """
        if self.last_modif and self.made_on < self.last_modif.made_on:
            return False, (
                f"The measurement cannot be older than the last film "
                f"modification you chose "
                f"({modif_label(self.last_modif)}, made on "
                f"{self.last_modif.made_on}).")
        if self._next_modif and self._next_modif.made_on < self.made_on:
            return False, (
                f"The film was modified again before this measurement "
                f"({modif_label(self._next_modif)}, made on "
                f"{self._next_modif.made_on}). Choose it as the last "
                f"modification, or fix the dates.")
        return True, ''

    def to_charac(self) -> Charac:
        """Build the unsaved `Charac` row, without its file or subtype.

        Doesn't check validity: `RootForm` calls it right away, so
        columns can be None while the form is incomplete.

        Returns:
            The characterization.
        """
        return Charac(
            made_on=self.made_on,
            made_by_email=self.made_by,
            comment=self.comment,
            type_=self.charac_type,
            film=self.film,
            last_modif=self.last_modif,
        )


class RootForm(Form):
    """The whole characterization form.

    Attributes:
        charac: The unsaved `Charac` with its subtype rows attached
            (`edxs`...) and its `file` set. None until the form is
            valid.
        charac_file: The unsaved `CharacFile`. None until the form is
            valid.
        file_stream: The data file, as an open binary file to give to
            `charac_file.save_stream()`. None until the form is valid.
    """

    def __init__(self, film: Film):
        """Draw the common fields, then the form of the chosen type.

        Args:
            film: The measured film.

        Raises:
            PausePageRun: While no type is chosen, so the data form is
                not drawn before.
        """
        st.header(film.label)
        st.header('New characterisation')
        base_info_form = CharacBaseInfoForm(film)
        if base_info_form.charac_type is None:
            raise PausePageRun

        st.divider()
        spec = CHARAC_TYPES[base_info_form.charac_type]
        data_form = spec.data_form()

        super().__init__(
            fields=[], sub_forms=[base_info_form, data_form])

        self.charac = None
        self.charac_file = None
        self.file_stream = None
        if self.is_valid:
            label = f'{spec.name} data'
            charac_file = CharacFile(
                label=label,
                internal_file_name=CharacFile.new_internal_file_name(
                    label, data_form.original_file_name),
                original_file_name=data_form.original_file_name,
                upload_date=date.today(),
            )
            charac = base_info_form.to_charac()
            charac.file = charac_file
            data_form.attach_to(charac)
            self.charac = charac
            self.charac_file = charac_file
            self.file_stream = data_form.file_stream

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''
