"""Top-level forms of the film modification page.

`RootForm` draws the information common to every modification
(`ModifBaseInfoForm`), then the sub-form of the chosen kind: annealing,
ion beam etching, wet etching or lift-off (from the sub-packages of
this folder). Its `film_modif` attribute is the unsaved object graph
(the modification and all its parts) that `pages/new_film_modif.py`
saves.
"""

import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.annealing.sub_forms import AnnealingForm
from components.forms.new_film_modif.fields import MadeOnField, MadeAfterField, \
    MadeByField, CommentField, ModifTypeField
from components.forms.new_film_modif.ion_beam_etching.sub_forms import \
    IonEtchingForm
from components.forms.new_film_modif.lift_off.sub_forms import LiftOffForm
from components.forms.new_film_modif.wet_etching.sub_forms import WetEtchingForm
from logic.constants import FILM_INIT_STATE, CookieKeys as Ck
from logic.cookie_init import cookies
from logic.lab_modelization.db_enums import FilmModifType
from logic.lab_modelization.db_models import (
    FilmModification, Film, AnnealingStep)


class ModifBaseInfoForm(Form):
    """Type, date, author, position in the history and comment of a
    modification.

    Attributes:
        modif_type: The chosen `FilmModifType`, or None.
        made_on: The date, or None.
        modif_number: Position the new modification takes in the
            film's history (0 = first), or None. Saving it shifts the
            later modifications up by one (see `FilmModification.save`).
        previous_modif: The modification before `default_modif` in the
            DB, or None. It does not follow the "Previous film
            modification" choice (see DOC_NOTES.md).
        made_by: The author's email address, or None.
        comment: The comment; `''` or None if empty.
    """

    def __init__(self, default_modif: FilmModification|None):
        """Draw the common fields.

        Reads the "last email used" cookie (a small value the browser
        stores for the app between visits) to prefill the author.

        Args:
            default_modif: Existing modification to prefill from (edit
                pages), or None.
        """
        modif_type_fld = ModifTypeField(
            form_default=None,
            db_default=None if default_modif is None
                else default_modif.modif_type,
        )
        with st.container(horizontal=True):
            made_on_fld = MadeOnField(
                form_default=None,
                db_default=None if default_modif is None
                    else default_modif.made_on,
            )

            made_by_fld = MadeByField(
                form_default=cookies.get(Ck.LAST_EMAIL_USED),
                db_default=default_modif.made_by_email
                    if default_modif else None,
            )

        previous_modif = default_modif.previous_modif if default_modif else None

        # Rebuild the `MadeAfterField` option that designates the
        # previous modification (see `MadeAfterField.get_options`).
        if default_modif and default_modif.modif_number == 0:
            made_after_db_default = FILM_INIT_STATE
        elif default_modif:
            made_after_db_default = (previous_modif.modif_number + 1,
                                     previous_modif.modif_type)
        else:
            made_after_db_default = None

        made_after_fld = MadeAfterField(
            form_default=None,
            db_default=made_after_db_default,
        )

        if made_after_fld.value is None:
            current_modif_number = None
        else:
            # This field returns a couple (see field select box options).
            # Its first item is already the previous modification's
            # number + 1 (0 for the initial state), i.e. the number the
            # new modification takes.
            made_after_idx, made_after_type = made_after_fld.value
            previous_modif_number = made_after_idx - 1
            current_modif_number = previous_modif_number + 1

        comment_fld = CommentField(
            form_default='',
            db_default=None if default_modif is None
                else default_modif.comment,
        )

        self.modif_type = modif_type_fld.value
        self.made_on = made_on_fld.value
        self.modif_number = current_modif_number
        # TODO `ModifBaseInfoForm.previous_modif` comes from `default_modif`, not from
        #   the "Previous film modification" choice. On the new-modification page
        #   it is always None, so the check "date not earlier than the previous
        #   modification" (`_is_coherent`, line 120) never runs.
        self.previous_modif = previous_modif
        self.made_by = made_by_fld.value
        self.comment = comment_fld.value

        super().__init__(
            fields=[modif_type_fld, made_on_fld, made_after_fld, made_by_fld,
                    comment_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """Refuse a date earlier than the previous modification's.

        Only checked when `previous_modif` is set, i.e. never on the
        new-modification page (see DOC_NOTES.md). See
        `Form._is_coherent`.
        """
        if self.previous_modif:
            if self.previous_modif.made_on > self.made_on:
                return False, ("The date of this modification cannot be "
                               "anterior to what has been selected as the "
                               "previous modification.")
        return True, ''

    def to_film_modif(self, film: Film):
        """Build the unsaved `FilmModification` row.

        Doesn't check validity: `RootForm` calls it right away, so
        columns can be None while the form is incomplete.

        Args:
            film: The modified film.

        Returns:
            The modification, without its subtype rows.
        """
        modif = FilmModification(
            made_on=self.made_on,
            modif_number=self.modif_number,
            made_by_email=self.made_by,
            comment=self.comment,
            modif_type=self.modif_type,
            film=film,
        )
        return modif


class RootForm(Form):
    """The whole film modification form.

    Attributes:
        film_modif: The unsaved `FilmModification` with its subtype
            rows attached (`annealings`, or `etchings` and below), ready
            for `save_with_dependent()`.
    """

    def __init__(self, default_film_modif: FilmModification|None, film: Film):
        """Draw the common fields, then the form of the chosen type.

        For an annealing, also plots the temperature profile.

        Args:
            default_film_modif: Existing modification to prefill from
                (edit pages), or None.
            film: The modified film.

        Raises:
            PausePageRun: While no type is chosen, and (from the
                sub-forms' `to_...` methods) while the chosen type's
                form is not valid. The page's "Submit" button is
                therefore only drawn once everything is valid.
        """
        st.header(film.label)
        st.header("Film Modification")
        base_info_form = ModifBaseInfoForm(default_film_modif)
        film_modif = base_info_form.to_film_modif(film)

        annealing_form, ion_etching_form = None, None

        if not film_modif.modif_type:
            raise PausePageRun

        st.divider()

        # Each case builds the subtype rows and attaches them to
        # `film_modif` as lists of length 1 (see "Subtypes" in
        # CLAUDE.md).
        match film_modif.modif_type:
            case FilmModifType.ANNEALING:
                if default_film_modif:
                    default_annealing = default_film_modif.annealings[0]
                else:
                    default_annealing = None
                annealing_form = AnnealingForm(default_annealing)
                annealing = annealing_form.to_annealing(film_modif)
                fig = AnnealingStep.get_figure(annealing.steps)
                st.plotly_chart(fig)
                film_modif.annealings = [annealing]

            case FilmModifType.ION_BEAM_ETCHING:
                if default_film_modif:
                    beam_etch = default_film_modif.etchings[0].ion_etchings[0]
                else:
                    beam_etch = None
                ion_etching_form = IonEtchingForm(beam_etch)
                etching = ion_etching_form.to_ion_etching(film_modif)
                film_modif.etchings = [etching]

            case FilmModifType.WET_ETCHING:
                if default_film_modif:
                    wet_etch = default_film_modif.etchings[0].wet_etchings[0]
                else:
                    wet_etch = None
                wet_etch_form = WetEtchingForm(wet_etch)
                etching = wet_etch_form.to_wet_etching(film_modif)
                film_modif.etchings = [etching]

            case FilmModifType.LIFT_OFF:
                if default_film_modif:
                    lift_off = default_film_modif.etchings[0].lift_offs[0]
                else:
                    lift_off = None
                lift_off_form = LiftOffForm(lift_off)
                etching = lift_off_form.to_lift_off_etching(film_modif)
                film_modif.etchings = [etching]

        self.film_modif = film_modif

        # The wet etching and lift-off forms are not listed here; their
        # validity is still enforced by the `PausePageRun` raised in
        # their `to_...` methods.
        super().__init__(
            fields=[],
            sub_forms=[base_info_form, annealing_form, ion_etching_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''
