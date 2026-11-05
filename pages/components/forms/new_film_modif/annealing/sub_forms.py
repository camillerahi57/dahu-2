"""Annealing part of the film modification form.

The user describes an annealing as a list of *phases*. A phase is
either a ramp (the temperature changes linearly up to a new value) or a
plateau (the temperature stays the same). The DB doesn't store phases
but `AnnealingStep`s, the points between phases, so `n` phases give
`n + 1` steps (see `PhaseListForm.to_steps`).

`AnnealingForm` is the entry point, used by `RootForm` in
`new_film_modif/sub_forms.py`. Its `default_...` arguments prefill the
form from an existing annealing; no page passes one yet, since there is
no page to edit a film modification.
"""

import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.fields import (
    PhaseTypeField, FurnaceField, \
    StartPressureField, PumpingDurationField, IsRoomTemperatureField, \
    ReachedTempField, PhaseDurationField, AnnealingAtmosphereField, \
    PhaseCountField, AtmosphereIsVacuumField)
from logic.lab_modelization.db_models import Annealing, FilmModification, \
    AnnealingStep, StoichioElement

# Short alias for the "Ramp" / "Plateau" enum.
phase_types = PhaseTypeField.Options


class AnnealingIntroForm(Form):
    """Furnace, start pressure and pumping time of an annealing.

    Attributes:
        furnace: The chosen `Furnace` value, or None.
        pressure: Start pressure, in Pa (typed in mbar), or None.
        pumping_duration: Pumping time before heating, in s (typed in
            min), or None.
    """

    def __init__(self, default_annealing: Annealing|None):
        """Draw the three fields side by side.

        Args:
            default_annealing: Existing annealing to prefill from, or
                None.
        """
        with st.container(horizontal=True):
            furnace_fld = FurnaceField(
                form_default=None,
                db_default=None if default_annealing is None
                    else default_annealing.furnace,
            )
            pressure_fld = StartPressureField(
                form_default=None,
                db_default=None if default_annealing is None
                    else default_annealing.pressure,
            )
            pumping_duration_fld = PumpingDurationField(
                form_default=None,
                db_default=None if default_annealing is None
                else default_annealing.pumping_duration,
            )
        self.furnace = furnace_fld.value
        self.pressure = pressure_fld.in_db_unit
        self.pumping_duration = pumping_duration_fld.in_db_unit

        super().__init__(
            fields=[furnace_fld, pressure_fld, pumping_duration_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''

    def to_annealing(self, film_modif: FilmModification):
        """Build an unsaved `Annealing` row, without its steps.

        Not called anywhere: `AnnealingForm.to_annealing` builds the
        row itself (see DOC_NOTES.md).

        Args:
            film_modif: The (unsaved) modification it belongs to.

        Returns:
            The annealing.
        """
        # TODO Not used. Delete this method?
        annealing = Annealing(
            pumping_duration=self.pumping_duration,
            pressure=self.pressure,
            furnace=self.furnace,
            film_modif=film_modif,
        )
        return annealing


class RampPhaseForm(Form):
    """The end point and duration of a ramp phase.

    A ramp ends either at room temperature (checkbox) or at a typed
    temperature.

    Attributes:
        is_room_temp: True if the ramp goes to room temperature.
        temperature: Temperature reached, in K (typed in °C); None when
            the ramp goes to room temperature or the field is invalid.
        duration: Duration of the phase, in s, or None.
    """

    def __init__(self, default_reached_temp: float|None,
                 default_duration: float|None,
                 default_is_room_temp: bool|None, key: str):
        """Draw the checkbox, the temperature (if needed) and duration.

        Args:
            default_reached_temp: Prefilled temperature, or None. The
                caller passes a DB value in K, but it is shown as °C
                without conversion (see the TODO below).
            default_duration: Prefilled duration, in s, or None.
            default_is_room_temp: Prefilled checkbox state, or None.
            key: Makes the widget keys of this phase unique on the page.
        """
        with st.container(horizontal=True, vertical_alignment='top',
                          gap='large'):
            is_room_temp_fld = IsRoomTemperatureField(
                key=key,
                form_default=default_is_room_temp,
            )
            # TODO passes DB values (K) to `ReachedTempField` as
            #   `form_default`, which is not converted (only
            #   `db_default` is), so an edit page would show kelvins
            #   labelled °C.
            # The temperature is only asked when the ramp doesn't go to
            # room temperature, so `disabled` below is always falsy.
            if is_room_temp_fld.value is not True:
                reached_temp_fld = ReachedTempField(
                    key=key,
                    form_default=default_reached_temp,
                    disabled=is_room_temp_fld.value,
                )

            else:
                reached_temp_fld = None

            # `PhaseDurationField.ui_unit` is the second, the DB unit, so
            # passing a DB duration as `form_default` happens to work.
            duration_fld = PhaseDurationField(
                key=key,
                form_default=default_duration,
            )

        self.is_room_temp = is_room_temp_fld.value
        self.temperature = reached_temp_fld.in_db_unit \
            if reached_temp_fld is not None \
            else None
        self.duration = duration_fld.in_db_unit

        super().__init__(
            fields=[is_room_temp_fld, reached_temp_fld, duration_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''


class PlateauPhaseForm(Form):
    """The duration of a plateau phase (its temperature is the
    previous one).

    Attributes:
        duration: Duration of the phase, in s, or None.
    """

    def __init__(self, default_duration: float|None, key: str):
        """Draw the duration field.

        Args:
            default_duration: Prefilled duration, in s, or None.
            key: Makes the widget key of this phase unique on the page.
        """
        duration_fld = PhaseDurationField(
            key=key,
            form_default=default_duration,
        )

        self.duration = duration_fld.in_db_unit

        super().__init__(fields=[duration_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''


class PhaseForm(Form):
    """One phase, in a bordered box: type, atmosphere, then the ramp or
    plateau form.

    Attributes:
        phase_type: `phase_types.RAMP` or `phase_types.PLATEAU`.
        atmosphere: Chemical formula of the gas, or None (empty or
            invalid).
        is_vacuum: True if the phase is under vacuum.
        ramp_form: The `RampPhaseForm` of a ramp, else None.
        plateau_form: The `PlateauPhaseForm` of a plateau, else None.
        duration: Duration of the phase, in s, or None.
    """

    def __init__(self,
                 default_reached_temp: float|None,
                 default_duration: float|None,
                 default_is_room_temp: bool|None,
                 default_phase_type: phase_types | None,
                 default_stoichio: str|None,
                 end_step: AnnealingStep|None,
                 phase_idx: int,
                 key: str, ):
        """Draw the phase box.

        Args:
            default_reached_temp: See `RampPhaseForm.__init__`.
            default_duration: Prefilled duration, in s, or None.
            default_is_room_temp: See `RampPhaseForm.__init__`.
            default_phase_type: Prefilled phase type, or None.
            default_stoichio: Prefilled atmosphere formula; `''` or
                None for none.
            end_step: Existing step at the end of this phase, used to
                prefill the vacuum checkbox, or None.
            phase_idx: Position of the phase, from 0 (shown from 1).
            key: Makes the widget keys of this phase unique on the page.

        Raises:
            PausePageRun: While the phase type is not chosen.
            RuntimeError: If the phase type is neither ramp nor plateau.
        """
        with st.container(border=True):
            with st.container(horizontal=True):
                st.subheader(f"Phase {phase_idx + 1}", width='content')
                phase_type_fld = PhaseTypeField(
                    key=key,
                    form_default=None,
                    db_default=default_phase_type,
                )
                atmosphere_fld = AnnealingAtmosphereField(
                    key=key,
                    form_default='',
                    db_default=default_stoichio,
                )
                is_vacuum_fld = AtmosphereIsVacuumField(
                    key=f'vacuum_{key}',
                    form_default=False,
                    db_default=end_step.preceding_was_vacuum
                        if end_step else None
                )

            phase_type = phase_type_fld.value
            if phase_type is None:
                raise PausePageRun

            if phase_type == phase_types.RAMP:
                phase_form = RampPhaseForm(
                    default_reached_temp=default_reached_temp,
                    default_duration=default_duration,
                    default_is_room_temp=default_is_room_temp,
                    key=key,
                )
            elif phase_type == phase_types.PLATEAU:
                phase_form = PlateauPhaseForm(default_duration, key)
            else:
                raise RuntimeError(f'Unknown phase type: {phase_type}.')

        self.phase_type = phase_type
        self.atmosphere: str|None = atmosphere_fld.value
        self.is_vacuum: bool = is_vacuum_fld.value
        if phase_type == phase_types.RAMP:
            self.ramp_form: RampPhaseForm|None = phase_form
            self.plateau_form = None
            self.duration = self.ramp_form.duration
        else:
            self.plateau_form: PlateauPhaseForm|None = phase_form
            self.ramp_form = None
            self.duration = self.plateau_form.duration

        super().__init__(fields=[phase_type_fld, atmosphere_fld, is_vacuum_fld],
                         sub_forms=[phase_form])

    def _is_coherent(self) -> tuple[bool, str]:
        """Require exactly one of "vacuum" and an atmosphere formula.

        See `Form._is_coherent`.
        """
        if self.is_vacuum and self.atmosphere:
            return False, ('Annealing atmosphere is vacuum but a stoichiometry '
                           'has been provided.')
        if not self.is_vacuum and not self.atmosphere:
            return False, 'Missing atmosphere stoichiometry (or check vacuum).'
        return True, ''

    def get_stoichio(self, annealing_step: AnnealingStep) \
            -> list[StoichioElement]:
        """Build the unsaved composition rows of the phase's atmosphere.

        Args:
            annealing_step: The step at the end of this phase; the rows
                become its `preceding_atmosphere`.

        Returns:
            One `StoichioElement` per element of the formula, or an
            empty list under vacuum.
        """
        if not self.atmosphere:
            return []
        return StoichioElement.from_str(
            formula=self.atmosphere,
            fk_field=StoichioElement.annealing_step,
            parent=annealing_step,
        )


class PhaseListForm(Form):
    """The phases of an annealing: a phase count, then one `PhaseForm`
    each.

    Attributes:
        phase_forms: One `PhaseForm` per phase, in time order.
    """

    def __init__(self, default_annealing: Annealing|None):
        """Draw the header, the phase count and the phase boxes.

        When editing, phase `i` is rebuilt from steps `i` and `i + 1`
        of `default_annealing`. If the user raises the count, the extra
        phases start empty.

        Args:
            default_annealing: Existing annealing to prefill from, or
                None.

        Raises:
            PausePageRun: While the phase count is empty or invalid
                (fewer than 2), and from `PhaseForm` while a phase type
                is not chosen.
        """
        st.header("Annealing Phases")
        phase_count_fld = PhaseCountField(
            form_default=0,
            db_default=0 if default_annealing is None
                else len(default_annealing.steps) - 1,
        )
        phase_count = phase_count_fld.value

        if phase_count is None:
            raise PausePageRun

        phase_forms: list[PhaseForm] = []
        for phase_idx in range(phase_count):

            default_reached_temp = None
            default_duration = None
            default_is_room_temp = False
            default_step_type = None
            default_stoichio = ''

            if default_annealing:
                # `steps` is a backref (the query of the steps pointing
                # to this annealing) without ORDER BY, so their order
                # isn't guaranteed (see DOC_NOTES.md).
                db_steps = default_annealing.steps  # TODO not ordered?
                try:
                    db_phase_start = db_steps[phase_idx]
                    db_phase_end = db_steps[phase_idx + 1]

                    default_stoichio = StoichioElement.to_str(
                        elements=db_steps[phase_idx + 1].preceding_atmosphere
                    )

                    default_reached_temp = db_phase_end.temperature

                    start_time = db_phase_start.timestamp
                    end_time = db_phase_end.timestamp
                    default_duration = end_time - start_time

                    default_is_room_temp = db_phase_end.is_room_temperature

                    # A ramp to the temperature it started from looks
                    # like a plateau here; both give the same steps.
                    if db_phase_start.is_plateau(db_phase_end):
                        default_step_type = phase_types.PLATEAU
                    else:
                        default_step_type = phase_types.RAMP

                # Phases beyond the existing ones start empty.
                except IndexError:
                    db_phase_end = None
            else:
                db_phase_end = None

            form = PhaseForm(
                default_reached_temp=default_reached_temp,
                default_duration=default_duration,
                default_is_room_temp=default_is_room_temp,
                default_phase_type=default_step_type,
                default_stoichio=default_stoichio,
                end_step=db_phase_end,
                phase_idx=phase_idx,
                key=f'step_{phase_idx}',
            )
            phase_forms.append(form)

        self.phase_forms = phase_forms

        super().__init__(fields=[phase_count_fld], sub_forms=phase_forms)

    def _is_coherent(self) -> tuple[bool, str]:
        """Require a ramp up first and a ramp to room temperature last.

        These match what `Annealing.assert_valid_annealing` expects.
        `PhaseCountField` ensures there are at least 2 phases. See
        `Form._is_coherent`.
        """
        first_phase = self.phase_forms[0]
        last_phase = self.phase_forms[-1]
        if first_phase.phase_type == phase_types.PLATEAU:
            return False, "First phase must be a ramp."
        if first_phase.ramp_form.is_room_temp:
            return False, ("First phase must be a ramp to another temperature "
                           "(not room temperature).")
        if last_phase.phase_type == phase_types.PLATEAU:
            return False, "Last phase must be a ramp to room temperature."
        if not last_phase.ramp_form.is_room_temp:
            return False, "Last phase must be a ramp to room temperature."
        return True, ''

    def to_steps(self, annealing: Annealing):
        """Turn the phases into unsaved `AnnealingStep` rows.

        The first step is at room temperature at time 0. Each phase
        then adds one step at the end of the phase: its timestamp is
        the sum of the durations so far (in s), and its temperature is
        the ramp's, or for a plateau the last ramp's. Each step gets
        the atmosphere of the phase that ends at it.

        Args:
            annealing: The (unsaved) annealing the steps belong to.

        Returns:
            The `phase count + 1` steps, in time order.

        Raises:
            PausePageRun: If the form is not valid.
        """
        if not self.is_valid:
            raise PausePageRun

        forms = self.phase_forms

        init_step = AnnealingStep(
            timestamp=0.,
            temperature=None,
            is_room_temperature=True,
            preceding_was_vacuum=None,
            annealing=annealing,
        )
        steps = [init_step]

        current_timestamp = 0.
        # `_is_coherent` makes the first phase a ramp, so a plateau
        # always finds a previous ramp here.
        last_ramp_form = None
        last_is_room_temp = True

        for idx, form in enumerate(forms):
            current_timestamp += form.duration

            if form.phase_type == phase_types.RAMP:
                temperature = form.ramp_form.temperature
                last_ramp_form = form.ramp_form
                last_is_room_temp = form.ramp_form.is_room_temp
            else:
                temperature = last_ramp_form.temperature

            step = AnnealingStep(
                timestamp=current_timestamp,
                temperature=temperature,
                is_room_temperature=last_is_room_temp,
                preceding_was_vacuum=form.is_vacuum,
                annealing=annealing,
            )
            step.preceding_atmosphere = form.get_stoichio(step)
            steps.append(step)

        return steps


class AnnealingForm(Form):
    """The whole annealing form: `AnnealingIntroForm`, then
    `PhaseListForm`.

    Attributes:
        intro_form: The furnace / pressure / pumping form.
        phase_list_form: The phases form.
    """

    def __init__(self, default_annealing: Annealing|None):
        """Draw both sub-forms, separated by a divider.

        Args:
            default_annealing: Existing annealing to prefill from, or
                None.

        Raises:
            PausePageRun: See `PhaseListForm.__init__`.
        """
        intro_form = AnnealingIntroForm(default_annealing)
        st.divider()
        phase_list_form = PhaseListForm(default_annealing)

        self.intro_form = intro_form
        self.phase_list_form = phase_list_form

        super().__init__(fields=[], sub_forms=[intro_form, phase_list_form])

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''

    def to_annealing(self, film_modif: FilmModification) -> Annealing:
        """Build the unsaved `Annealing` row with its steps.

        Args:
            film_modif: The (unsaved) modification it belongs to.

        Returns:
            The annealing, with `steps` set (and their atmospheres),
            ready for `save_with_dependent()`.

        Raises:
            PausePageRun: If the form is not valid.
        """
        if not self.is_valid:
            raise PausePageRun

        annealing = Annealing(
            pumping_duration=self.intro_form.pumping_duration,
            pressure=self.intro_form.pressure,
            furnace=self.intro_form.furnace,
            film_modif=film_modif,
        )
        steps = self.phase_list_form.to_steps(annealing)
        annealing.steps = steps
        return annealing
