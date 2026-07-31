import streamlit as st

from components.forms.new_film_modif.ion_beam_etching.sub_forms import \
    IonEtchingForm
from components.forms.new_film_modif.annealing.sub_forms import AnnealingForm
from components.forms.new_film_modif.fields import MadeOnField, MadeAfterField,\
    MadeByField, CommentField, ModifTypeField
from components.forms.base_classes import Form, PausePageRun
from logic.constants import FILM_INIT_STATE
from logic.db_enums import FilmModifType
from logic.lab_modelization.db_models import (
    FilmModification, Film, AnnealingStep)


class ModifBaseInfoForm(Form):
    def __init__(self, default_modif: FilmModification|None):
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
                form_default='',
                db_default=None if default_modif is None
                    else default_modif.made_by_email,
            )

        made_after_db_default = None
        previous_modif = None
        if default_modif is not None:
            if default_modif.modif_number == 0:
                made_after_db_default = (-1, FILM_INIT_STATE)
            else:
                previous_modif = default_modif.previous_modif
                made_after_db_default = (
                    previous_modif.modif_number,
                    previous_modif.modif_type,
                )
        made_after_fld = MadeAfterField(
            form_default=None,
            db_default=made_after_db_default,
        )
        if made_after_fld.value is None:
            modif_nb = None
        else:
            # This field returns a couple (see field select box options).
            made_after_idx, made_after_type = made_after_fld.value
            modif_nb = made_after_idx + 1

        comment_fld = CommentField(
            form_default='',
            db_default=None if default_modif is None
                else default_modif.comment,
        )

        self.modif_type = modif_type_fld.value
        self.made_on = made_on_fld.value
        self.modif_number = modif_nb
        self.previous_modif = previous_modif
        self.made_by = made_by_fld.value
        self.comment = comment_fld.value

        super().__init__(
            fields=[modif_type_fld, made_on_fld, made_after_fld, made_by_fld,
                    comment_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        if self.previous_modif is not None:
            if self.previous_modif.made_on > self.made_on:
                return False, ("The date of this modification cannot be "
                               "anterior to what has been selected as the "
                               "previous modification.")
        return True, ''

    def to_film_modif(self, film: Film):
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
    def __init__(self, default_film_modif: FilmModification|None, film: Film):
        st.header(film.label)
        st.header("Film Modification")
        base_info_form = ModifBaseInfoForm(default_film_modif)
        film_modif = base_info_form.to_film_modif(film)

        annealing_form, ion_etching_form = None, None

        if not film_modif.modif_type:
            raise PausePageRun

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
                    default_etching = default_film_modif.ion_beam_etchings[0]
                else:
                    default_etching = None
                ion_etching_form = IonEtchingForm(default_etching)
                ion_etching = (ion_etching_form
                                            .to_ion_etching(film_modif))
                film_modif.ion_beam_etchings = [ion_etching]

        self.film_modif = film_modif

        super().__init__(
            fields=[],
            sub_forms=[base_info_form, annealing_form, ion_etching_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''
