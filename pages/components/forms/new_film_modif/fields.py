"""Input fields of the film modification forms (new-modification page).

Each class is one widget; see `Field` in
`components/forms/base_classes.py` for how fields draw and validate
themselves. They are assembled in `sub_forms.py` (fields common to
every modification), `shared.py` (fields common to every etching) and
the `annealing/`, `ion_beam_etching/`, `wet_etching/` and `lift_off/`
sub-packages.

Several classes are also imported by the models in
`logic/lab_modelization/db_models.py` (`title_db_value_input_fields`,
`AnnealingStep.get_figure`) to display DB values in the UI unit, so
changing a `ui_unit` here also changes how stored values are shown.

Many `_streamlit_input` methods don't pass `key` to their widget.
Streamlit then builds the widget key (the name it uses to recognize a
widget from one run to the next) from the label and parameters, so
such a field can appear only once per page.
"""

from enum import StrEnum
from typing import Iterable

import streamlit as st

from components.forms.base_classes import Field, FieldType as Ft, UnitField
from logic.constants import SessionKeys as Sk, FILM_INIT_STATE
from logic.global_variables import sess
from logic.lab_modelization.db_enums import FilmModifType, Furnace, \
    ChemicalElement, \
    EtchingBaseSuggestion, EtchingAcidSuggestion, EtchingSolventSuggestion, \
    IbeMachine
from logic.lab_modelization.db_models import FilmModification, Patch, \
    Pattern, Recipe
from logic.units import ur
from logic.utils import is_valid_email_address, all_email_addresses

# TODO `IonDurationField`,
#   `PreEtchDurationField`, `DcGridCurrentField`, `HardBakeTempField`,
#   `AcidEtchingDurationField` and `DevelopmentDurationField` pass
#   `min_value=0` (an int) to `st.number_input`, so Streamlit most likely
#   accepts only whole numbers (no 0.5 A grid current, no 1.5 min).

# TODO `MadeOnField`,
#   `FurnaceField` (line 518), `PlasmaFormulaField` (line 696),
#   `PlasmaProportionField` (line 718) and `ConstituentCountField`
#   (line 855) ignore `prefill`, so an edit page would not prefill them.

class MadeByField(Field):
    """Mandatory email address of the person who made the modification.

    A select box listing the addresses already known to the app
    (`all_email_addresses`); a new address can be typed. See
    `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box that accepts new entries; `key` is not used.

        `prefill` is preselected only if it is a known address. See
        `Field._streamlit_input`.
        """
        options = all_email_addresses
        index = options.index(prefill) if prefill in options else None
        return st.selectbox(
            "Made by (email address)",
            options=options, index=index, accept_new_options=True, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse invalid email addresses. See `Field._validate`."""
        if not is_valid_email_address(input_):
            return False, 'Please enter a valid email address.'
        return True, ''


class MadeOnField(Field):
    """Mandatory day the modification was made; no future dates.

    Any date is accepted. See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw a date picker, starting at today.

        `prefill` and `key` are not used (see DOC_NOTES.md). See
        `Field._streamlit_input`.
        """
        return st.date_input("Made on",
                             max_value='today')

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any date. See `Field._validate`."""
        return True, ''


class ModifTypeField(Field):
    """Mandatory kind of modification, a `FilmModifType` value.

    The choice decides which sub-form `RootForm` draws next. See
    `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw horizontal radio buttons; `key` is not used.

        See `Field._streamlit_input`.
        """
        options = list(FilmModifType)
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.radio('Modification type', options=FilmModifType,
                     index=index, horizontal=True)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse an empty choice. See `Field._validate`."""
        if input_ is None or input_ == '':
            return False, 'Please select a modification type.'
        return True, ''


class MadeAfterField(Field):
    """Mandatory choice of where the modification goes in the film's
    history.

    Each option is a pair `(position, modif_type)`. `FILM_INIT_STATE`
    `(0, 'Initial state (as deposited)')` means "before every existing
    modification"; an existing modification number `n` gives
    `(n + 1, its modif_type)`, meaning "right after it". The first item
    of the chosen pair is therefore the `modif_number` the new
    modification gets (see `ModifBaseInfoForm`). See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box of `get_options()`; `key` is not used.

        See `Field._streamlit_input`.
        """
        options = self.get_options()
        index = options.index(prefill) if prefill in options else None
        return st.selectbox(
            'Previous film modification (if any):',
            options=options, index=index, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse an empty choice. See `Field._validate`."""
        if input_ is None or input_ == '':
            return False, 'Please select an option.'
        return True, ''

    @staticmethod
    def get_options() -> list[str]:  # TODO Wring return annotation?
        """List the positions the new modification can take.

        Reads the film from `st.session_state[SessionKeys.CURRENT_FILM]`
        (the session state is a dictionary Streamlit keeps for each
        browser tab across reruns), which the page sets before drawing
        the form. Queries the DB for the film's modifications.

        Returns:
            `FILM_INIT_STATE`, then one `(modif_number + 1, modif_type)`
            pair per existing modification, in `modif_number` order.
            (The return annotation says `list[str]`, but the items are
            pairs.)
        """
        film = sess[Sk.CURRENT_FILM]
        film_modifs = (FilmModification.select()
                       .where(FilmModification.film == film))
        def get_modif_count(fm: FilmModification):
            """Sort key: the modification's position in the history.

            Args:
                fm: A modification of the film.

            Returns:
                Its `modif_number`.
            """
            return fm.modif_number
        film_modifs: Iterable[FilmModification] = sorted(list(film_modifs),
                                                         key=get_modif_count)
        options = [(modif.modif_number + 1, modif.modif_type)
                   for modif in film_modifs]
        options = [FILM_INIT_STATE] + options
        return options


class CommentField(Field):
    """Optional free-text comment on the modification.

    Any text is accepted. See `Field._validate`.
    """

    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        """Draw a full-width text area; `key` is not used.

        See `Field._streamlit_input`.
        """
        return st.text_area('Comment', value=prefill, width=99999)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any text. See `Field._validate`."""
        return True, ''


class PhaseDurationField(UnitField):
    """Mandatory duration of one annealing phase, typed in s.

    Stored in the DB in s (as differences of `AnnealingStep.timestamp`).
    Must be strictly positive. Its `ui_unit` is also the time axis unit
    of `AnnealingStep.get_figure`. See `Field._validate`.
    """

    type = Ft.MANDATORY
    ui_unit = ur.seconds

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0). See `Field._streamlit_input`."""
        return st.number_input(f'Phase duration (**{self.ui_unit}**)',
                               min_value=0., value=prefill, key=key, width=150)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if input_ == 0:
            return False, 'Duration must be strictly positive.'
        return True, ''


class PumpingDurationField(UnitField):
    """Mandatory pumping time before an annealing, typed in min.

    Stored in the DB in s (`Annealing.pumping_duration`). Must be
    strictly positive. See `Field._validate`.
    """

    type = Ft.MANDATORY
    ui_unit = ur.minutes

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0); `key` is not used.

        See `Field._streamlit_input`.
        """
        return st.number_input(f'Pumping duration (**{self.ui_unit}**)',
                               min_value=0., value=prefill, width=200)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if input_ == 0:
            return False, 'Duration must be strictly positive.'
        return True, ''


class StartPressureField(UnitField):
    """Advised pressure at the start of an annealing or ion beam
    etching, typed in mbar.

    Stored in the DB in Pa (`Annealing.pressure`,
    `IonBeamEtching.start_pressure`). Must be strictly positive. See
    `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.millibar

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0) that keeps up to 12 significant
        digits.

        The tiny `step` and the `'%.12g'` format let the user type
        values such as `3e-7` without Streamlit rounding them. See
        `Field._streamlit_input`.
        """
        return st.number_input(
            f'Start pressure (**{self.ui_unit}**)', min_value=0., width=300,
            value=prefill, key=key, step=0.0000000000001, format='%.12g',
            placeholder="You can use the '3e-7' notation."
        )

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if input_ == 0:
            return False, 'Pressure must be strictly positive.'
        return True, ''


class TargetPressureField(UnitField):
    """Advised aimed pressure of an ion beam etching, typed in mbar.

    Stored in the DB in Pa (`IonBeamEtching.target_pressure`). Must be
    strictly positive. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.millibar

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0) that keeps up to 12 significant
        digits.

        See `StartPressureField._streamlit_input` and
        `Field._streamlit_input`.
        """
        return st.number_input(
            f'Target pressure (**{self.ui_unit}**)', min_value=0., width=300,
            value=prefill, key=key, step=0.0000000000001, format='%.12g',
            placeholder="You can use the '3e-7' notation."
        )

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if input_ == 0:
            return False, 'Pressure must be strictly positive.'
        return True, ''


class AnnealingAtmosphereField(Field):
    """Advised chemical formula of the gas during one annealing phase.

    Left empty when the phase is under vacuum (`PhaseForm` checks that
    exactly one of the two is given). Validated by
    `Patch.is_valid_formula`. See `Field._validate`.
    """

    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        """Draw a text input. See `Field._streamlit_input`."""
        return st.text_input(
            'Atmosphere stoichiometry:', value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Check the formula syntax. See `Field._validate`."""
        return Patch.is_valid_formula(self._input)


class AtmosphereIsVacuumField(Field):
    """Optional checkbox: the annealing phase was under vacuum.

    Stored in `AnnealingStep.preceding_was_vacuum`. See
    `Field._validate`.
    """

    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        """Draw a checkbox. See `Field._streamlit_input`."""
        return st.checkbox('**Vacuum**',
                           value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept both states. See `Field._validate`."""
        return True, ''



class FlowField(UnitField):
    """Advised gas flow of an ion beam etching, typed in SCCM.

    SCCM ("standard cubic centimetres per minute") is handled as plain
    cm³/min; the DB stores m³/s (`IonBeamEtching.flow`). Must be
    strictly positive. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.cm**3 / ur.min
    ui_unit_alias = 'SCCM'

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0). See `Field._streamlit_input`."""
        return st.number_input(f'Flow ({self.ui_unit_alias})', min_value=0.,
                               value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if input_ == 0:
            return False, 'Flow must be strictly positive.'
        return True, ''


class AngleField(UnitField):
    """Advised beam incidence angle of an ion beam etching, typed in
    degrees.

    Stored in the DB in rad (`IonBeamEtching.incidence_angle`). Any
    value, negative included, is accepted. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.degrees

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input. See `Field._streamlit_input`."""
        return st.number_input(f'Angle (**{self.ui_unit}**)',
                               value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any number. See `Field._validate`."""
        return True, ''


class RotationSpeedField(UnitField):
    """Advised sample rotation speed of an ion beam etching, typed in
    rpm.

    Stored in the DB in rad/s (`IonBeamEtching.rotation`). Any value is
    accepted. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.rpm

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input. See `Field._streamlit_input`."""
        return st.number_input(f'Rotation speed (**{self.ui_unit}**)',
                               value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any number. See `Field._validate`."""
        return True, ''


class HasPatternField(Field):
    """Mandatory Yes/No: the etching used a pattern.

    `PatternForm` turns the answer into the boolean
    `Etching.has_a_pattern`. Both answers are accepted. See
    `Field._validate`.
    """

    type = Ft.MANDATORY

    class Option(StrEnum):
        """The two answers shown as radio buttons."""

        YES = 'Yes'
        NO = 'No'

    def _streamlit_input(self, prefill: str, key):
        """Draw horizontal Yes/No radio buttons; `key` is not used.

        `prefill` must be an `Option` value (see DOC_NOTES.md). See
        `Field._streamlit_input`.
        """
        options = list(self.Option)
        index = options.index(prefill) if prefill else None
        return st.radio('Has a pattern', options, horizontal=True,
                        index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept both answers. See `Field._validate`."""
        return True, ''


class SelectPatternLabelField(Field):
    """Optional choice of an uploaded `Pattern` file, by label.

    Patterns are uploaded on their own page, not here. See
    `Field._validate`.
    """

    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box of all pattern labels; `key` is not used.

        Side effect: queries the DB for all patterns. See
        `Field._streamlit_input`.
        """
        patterns: Iterable[Pattern] = Pattern.select()
        options = [p.label for p in patterns]
        index = options.index(prefill) if prefill else None
        return st.selectbox('Pattern', options, index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any choice. See `Field._validate`."""
        return True, ''


# class PatternLabelField(Field):
#     type = Ft.MANDATORY
#
#     def _streamlit_input(self, prefill, key: str):
#         return st.text_input('Pattern label', value=prefill)
#
#     def _validate(self, input_) -> tuple[bool, str]:
#         if input_ and Pattern.label_is_taken(input_):
#             return False, 'Label is already taken.'
#         return True, ''


class SelectRecipeLabelField(Field):
    """Optional choice of an uploaded `Recipe` file, by label.

    Recipes are uploaded on their own page, not here. See
    `Field._validate`.
    """

    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box of all recipe labels; `key` is not used.

        `prefill` must be a label (see DOC_NOTES.md). Side effect:
        queries the DB for all recipes. See `Field._streamlit_input`.
        """
        recipes: Iterable[Recipe] = Recipe.select()
        options = [r.label for r in recipes]
        index = options.index(prefill) if prefill else None
        return st.selectbox('Recipe',
                            options, index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any choice. See `Field._validate`."""
        return True, ''


class FurnaceField(Field):
    """Advised furnace used for an annealing, a `Furnace` value.

    See `Field._validate`.
    """

    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box of the `Furnace` values, starting empty.

        `prefill` and `key` are not used (see DOC_NOTES.md). See
        `Field._streamlit_input`.
        """
        options = [f.value for f in Furnace]
        return st.selectbox('Furnace', options, index=None,
                            )

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse an empty choice. See `Field._validate`."""
        # `_validate` only runs on a filled field, so this never fails.
        if input_ is None or input_ == '':
            return False, 'Please select a furnace.'
        return True, ''


class PowerField(UnitField):
    """Advised RF power of an ion beam etching, typed in W.

    Stored in the DB in W (`IonBeamEtching.power`). Must be strictly
    positive. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.watt

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0). See `Field._streamlit_input`."""
        return st.number_input(f'Power RF (**{self.ui_unit}**)', min_value=0.,
                               value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0 (and None). See `Field._validate`."""
        if input_ is None or input_ <= 0.:
            return False, 'Power must be strictly positive.'
        return True, ''


class ReachedTempField(UnitField):
    """Mandatory temperature reached at the end of an annealing ramp,
    typed in °C.

    Stored in the DB in K (`AnnealingStep.temperature`). Its `ui_unit`
    is also the temperature axis unit of `AnnealingStep.get_figure`.
    Any value is accepted. See `Field._validate`.

    Attributes:
        disabled: Whether the widget is greyed out.
    """

    type = Ft.MANDATORY
    ui_unit = ur.celsius

    def __init__(self, key: str|int = 'default_key', *, form_default,
                 db_default=None, disabled: bool):
        """Store `disabled`, then draw the field.

        Args:
            key: See `Field.__init__`.
            form_default: See `UnitField.__init__` (in °C).
            db_default: See `UnitField.__init__` (in K).
            disabled: True to grey out the widget. `RampPhaseForm`
                passes the "Goes to room temperature" checkbox value.
        """
        self.disabled = disabled  # Adding this parameter to the init method.
        super().__init__(
            key=key,
            form_default=form_default,
            db_default=db_default,
        )

    def _streamlit_input(self, prefill, key):
        """Draw a number input, possibly disabled.

        See `Field._streamlit_input`.
        """
        # `~P`: Pint's short and "pretty" format, e.g. °C.
        unit_str = f'{self.ui_unit:~P}'
        # unit_str = f'{self.ui_unit:~P}'
        return st.number_input(f"Reached temperature ({unit_str}):",
                               value=prefill,
                               key=key, disabled=self.disabled, width=175)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any number. See `Field._validate`."""
        return True, ''


class PhaseTypeField(Field):
    """Mandatory kind of annealing phase: ramp or plateau.

    A ramp changes the temperature linearly up to a new value; a
    plateau keeps the previous temperature. See `Field._validate`.
    """

    type = Ft.MANDATORY

    class Options(StrEnum):
        """The two phase kinds shown as radio buttons."""

        RAMP = 'Ramp'
        PLATEAU = 'Plateau'

    def _streamlit_input(self, prefill, key: str):
        """Draw horizontal radio buttons. See `Field._streamlit_input`."""
        options = list(self.Options)
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.radio(
            'Annealing phase type', options=options, index=index, key=key,
            horizontal=True
        )

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept both kinds. See `Field._validate`."""
        return True, ''


class PhaseCountField(Field):
    """Mandatory number of annealing phases; at least 2.

    A phase is the time between two `AnnealingStep`s, so `n` phases
    give `n + 1` steps. See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw an integer input (>= 0); `key` is not used.

        See `Field._streamlit_input`.
        """
        return st.number_input('Number of annealing phases', min_value=0,
                               value=prefill, step=1, width=200)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse fewer than 2 phases. See `Field._validate`."""
        # 2 phases = 3 steps, the minimum `Annealing.assert_valid_annealing`
        # accepts.
        if input_ < 2:
            return False, (
                'There must be at least 2 phases: room temperature to annealing'
                ' temperature, then back to room temperature.'
            )
        return True, ''


class IsRoomTemperatureField(Field):
    """Optional checkbox: the annealing ramp ends at room temperature.

    Stored in `AnnealingStep.is_room_temperature`; when checked, no
    temperature is asked. See `Field._validate`.
    """

    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        """Draw a checkbox. See `Field._streamlit_input`."""
        return st.checkbox('**Goes to room temperature**',
                           value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept both states. See `Field._validate`."""
        return True, ''


class PlasmaFormulaField(Field):
    """Mandatory chemical formula of one ion beam etching plasma gas.

    Validated by `Patch.is_valid_formula`. See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw a text input that starts at `'Ar'`.

        `prefill` is not used (see DOC_NOTES.md). See
        `Field._streamlit_input`.
        """
        return st.text_input('Formula',
                             key=key, value=ChemicalElement.ARGON)

    def _validate(self, input_) -> tuple[bool, str]:
        """Check the formula syntax. See `Field._validate`."""
        return Patch.is_valid_formula(input_)


class PlasmaProportionField(Field):
    """Mandatory relative amount of one plasma gas; no unit.

    Any positive number: `ConstituentListForm.to_plasma` divides by the
    sum of all proportions, so only the ratios matter. See
    `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0) that starts at 1.

        `prefill` is not used (see DOC_NOTES.md). See
        `Field._streamlit_input`.
        """
        return st.number_input(
            'Proportion (will be normalized)', min_value=0., value=1.,
            key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Proportion must be strictly positive.'
        return True, ''

# TODO `BaseField`,
#   `AcidField` and `SolventField` (line 801) accept typed names, but
#   prefilling with a name that is not a suggestion makes `options.index`
#   raise `ValueError`. Also, `wet_etching/sub_forms.py:152` passes an
#   `EtchingSolvent` object (not its `label`) as `SolventField` default.

class BaseField(Field):
    """Optional base used in a wet etching (`WetEtching.base`).

    The list offers `EtchingBaseSuggestion` values, but any name can be
    typed. See `Field._validate`.
    """

    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box that accepts new entries.

        `prefill` must be one of the suggestions (see DOC_NOTES.md).
        See `Field._streamlit_input`.
        """
        options = list(EtchingBaseSuggestion)
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox('Base', options=options, index=index, key=key,
                            accept_new_options=True)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any name. See `Field._validate`."""
        return True, ''


class AcidField(Field):
    """Optional acid used in a wet etching (`WetEtching.acid`).

    The list offers `EtchingAcidSuggestion` values, but any name can be
    typed. See `Field._validate`.
    """

    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box that accepts new entries.

        `prefill` must be one of the suggestions (see DOC_NOTES.md).
        See `Field._streamlit_input`.
        """
        options = list(EtchingAcidSuggestion)
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox('Acid', options=options, index=index, key=key,
                            accept_new_options=True)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any name. See `Field._validate`."""
        return True, ''


class SolventField(Field):
    """Mandatory name of one solvent of a wet etching
    (`EtchingSolvent.label`).

    The list offers `EtchingSolventSuggestion` values, but any name can
    be typed. One field is drawn per solvent, each with its own `key`.
    See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box without label that accepts new entries.

        The label is hidden because `SolventListForm` writes
        "Solvent i" above it. `prefill` must be one of the suggestions
        (see DOC_NOTES.md). See `Field._streamlit_input`.
        """
        options = list(EtchingSolventSuggestion)
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox(
            'Solvent', options=options, index=index, key=key,
            accept_new_options=True, label_visibility='collapsed')

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any name. See `Field._validate`."""
        return True, ''


class SolventCountField(Field):
    """Optional number of solvents of a wet etching; at least 1.

    Decides how many `SolventField`s `SolventListForm` draws. See
    `Field._validate`.
    """

    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        """Draw an integer input (>= 1); `key` is not used.

        See `Field._streamlit_input`.
        """
        return st.number_input('Number of solvents', value=prefill,
                               min_value=1, step=1)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any count. See `Field._validate`."""
        return True, ''


class ConstituentCountField(Field):
    """Mandatory number of plasma gases of an ion beam etching; at
    least 1.

    Decides how many `ConstituentForm`s `ConstituentListForm` draws.
    See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw an integer input (>= 1) that starts at 1.

        `prefill` and `key` are not used (see DOC_NOTES.md). See
        `Field._streamlit_input`.
        """
        return st.number_input('Number of constituents', value=1,
                               step=1, min_value=1)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse fewer than 1 constituent. See `Field._validate`."""
        if input_ < 1:
            return False, 'There must be at least 1 constituent.'
        return True, ''


class IonDurationField(UnitField):
    """Advised duration of an ion beam etching, typed in s.

    Stored in the DB in s (`IonBeamEtching.duration`). Must be strictly
    positive. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.seconds

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0). See `Field._streamlit_input`."""
        # `min_value=0` is an int, so Streamlit only accepts whole
        # numbers here (see DOC_NOTES.md).
        return st.number_input(f'Duration (**{self.ui_unit}**)', min_value=0,
                               value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Must be strictly positive.'
        return True, ''

class PreEtchDurationField(UnitField):
    """Advised pre-etching duration of an ion beam etching, typed in s.

    Stored in the DB in s (`IonBeamEtching.pre_etching_duration`). Must
    be strictly positive. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.seconds

    def _streamlit_input(self, prefill, key: str):
        """Draw a whole-number input (>= 0).

        See `IonDurationField._streamlit_input` and
        `Field._streamlit_input`.
        """
        return st.number_input(f'Pre-etching duration (**{self.ui_unit}**)',
                               min_value=0, value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Must be strictly positive.'
        return True, ''


class DcGridCurrentField(UnitField):
    """Advised DC grid current of an ion beam etching, typed in A.

    Stored in the DB in A (`IonBeamEtching.dc_grid_current`). Must be
    strictly positive. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill, key: str):
        """Draw a whole-number input (>= 0).

        See `IonDurationField._streamlit_input` and
        `Field._streamlit_input`.
        """
        return st.number_input(f'DC grid current (**{self.ui_unit}**)',
                               min_value=0, value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Must be strictly positive.'
        return True, ''


class HardBakeTempField(UnitField):
    """Advised hard bake temperature of a wet etching, typed in °C.

    Stored in the DB in K (`WetEtching.hard_bake_temperature`). Must be
    strictly positive in °C. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.celsius

    def _streamlit_input(self, prefill, key: str):
        """Draw a whole-number input (>= 0 °C).

        See `IonDurationField._streamlit_input` and
        `Field._streamlit_input`.
        """
        return st.number_input(f'Hard bake temperature (**{self.ui_unit}**)',
                               min_value=0, value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0 °C. See `Field._validate`."""
        if self._input <= 0:
            return False, 'Hard bake temperature must be strictly positive.'
        return True, ''


class AcidEtchingDurationField(UnitField):
    """Advised time in the acid during a wet etching, typed in min.

    Stored in the DB in s (`WetEtching.etching_duration`). Must be
    strictly positive. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.minutes

    def _streamlit_input(self, prefill, key: str):
        """Draw a whole-number input (>= 0).

        See `IonDurationField._streamlit_input` and
        `Field._streamlit_input`.
        """
        return st.number_input(f'Acid etching duration (**{self.ui_unit}**)',
                               min_value=0, value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if self._input <= 0:
            return False, 'Acid etching duration must be strictly positive.'
        return True, ''


class DevelopmentDurationField(UnitField):
    """Advised development time of a wet etching, typed in min.

    Stored in the DB in s (`WetEtching.development_duration`). Must be
    strictly positive. See `Field._validate`.
    """

    type = Ft.ADVISED
    ui_unit = ur.minutes

    def _streamlit_input(self, prefill, key: str):
        """Draw a whole-number input (>= 0).

        See `IonDurationField._streamlit_input` and
        `Field._streamlit_input`.
        """
        return st.number_input(f'Development duration (**{self.ui_unit}**)',
                               min_value=0, value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if self._input <= 0:
            return False, 'Development duration must be strictly positive.'
        return True, ''


class UsedUltrasoundField(Field):
    """Mandatory Yes/No: ultrasound was used (wet etching or lift-off).

    The sub-forms turn the answer into the boolean `used_ultrasound`
    column. Both answers are accepted. See `Field._validate`.
    """

    type = Ft.MANDATORY

    class Option(StrEnum):
        """The two answers shown as radio buttons."""

        YES = 'Yes'
        NO = 'No'

    def _streamlit_input(self, prefill: str, key):
        """Draw horizontal Yes/No radio buttons; `key` is not used.

        `prefill` must be an `Option` value (see DOC_NOTES.md). See
        `Field._streamlit_input`.
        """
        options = list(self.Option)
        index = options.index(prefill) if prefill else None
        return st.radio('Used ultrasound', options, horizontal=True,
                        index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept both answers. See `Field._validate`."""
        return True, ''


class IbeMachineField(Field):
    """Mandatory ion beam etching machine, an `IbeMachine` value.

    See `Field._validate`.
    """

    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key: str):
        """Draw a select box of the machines; `key` is not used.

        See `Field._streamlit_input`.
        """
        options = list(IbeMachine)
        index = options.index(prefill) if prefill else None
        return st.selectbox('Machine', options, index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any machine. See `Field._validate`."""
        return True, ''


class UltrasoundConfigField(Field):
    """Advised free description of the ultrasound settings.

    Any text is accepted. See `Field._validate`.
    """

    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key: str):
        """Draw a text area. See `Field._streamlit_input`."""
        return st.text_area('Ultrasound config', value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any text. See `Field._validate`."""
        return True, ''


class EtchingDepthSpeedField(UnitField):
    """Optional acid etching speed into the depth, typed in µm/s.

    Stored in the DB in m/s (`WetEtching.acid_etching_depth_speed`).
    Must be strictly positive. See `Field._validate`.
    """

    type = Ft.OPTIONAL
    ui_unit = ur.microns / ur.second

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0) with steps of 0.001.

        See `Field._streamlit_input`.
        """
        return st.number_input(f'Etching depth speed (**{self.ui_unit}**)',
                               min_value=0., value=prefill, key=key, step=0.001)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if self._input <= 0:
            return False, 'Etching depth speed must be strictly positive.'
        return True, ''


class EtchingLateralSpeedField(UnitField):
    """Optional lateral acid etching speed, typed in µm/s.

    Stored in the DB in m/s (`WetEtching.acid_etching_lateral_speed`).
    Must be strictly positive. See `Field._validate`.
    """

    type = Ft.OPTIONAL
    ui_unit = ur.microns / ur.second

    def _streamlit_input(self, prefill, key: str):
        """Draw a number input (>= 0) with steps of 0.001.

        See `Field._streamlit_input`.
        """
        return st.number_input(f'Etching lateral speed (**{self.ui_unit}**)',
                               min_value=0., value=prefill, key=key, step=0.001)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0. See `Field._validate`."""
        if self._input <= 0:
            return False, 'Etching lateral speed must be strictly positive.'
        return True, ''


