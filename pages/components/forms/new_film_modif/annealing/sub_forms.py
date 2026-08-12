import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.fields import (
    PhaseTypeField, FurnaceField, \
    PressureField, PumpingDurationField, IsRoomTemperatureField, \
    ReachedTempField, PhaseDurationField, AnnealingAtmosphereField, \
    PhaseCountField, AtmosphereIsVacuumField)
from logic.lab_modelization.db_models import Annealing, FilmModification, \
    AnnealingStep, StoichioElement

phase_types = PhaseTypeField.Options


class AnnealingIntroForm(Form):
    def __init__(self, default_annealing: Annealing|None):
        with st.container(horizontal=True):
            furnace_fld = FurnaceField(
                form_default=None,
                db_default=None if default_annealing is None
                    else default_annealing.furnace,
            )
            pressure_fld = PressureField(
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
        return True, ''

    def to_annealing(self, film_modif: FilmModification):
        annealing = Annealing(
            pumping_duration=self.pumping_duration,
            pressure=self.pressure,
            furnace=self.furnace,
            film_modif=film_modif,
        )
        return annealing


class RampPhaseForm(Form):
    def __init__(self, default_reached_temp: float|None,
                 default_duration: float|None,
                 default_is_room_temp: bool|None, key: str):
        with st.container(horizontal=True, vertical_alignment='top',
                          gap='large'):
            is_room_temp_fld = IsRoomTemperatureField(
                key=key,
                form_default=default_is_room_temp,
            )
            if is_room_temp_fld.value is not True:
                reached_temp_fld = ReachedTempField(
                    key=key,
                    form_default=default_reached_temp,
                    disabled=is_room_temp_fld.value,
                )

            else:
                reached_temp_fld = None

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
        return True, ''


class PlateauPhaseForm(Form):
    def __init__(self, default_duration: float|None, key: str):
        duration_fld = PhaseDurationField(
            key=key,
            form_default=default_duration,
        )

        self.duration = duration_fld.in_db_unit

        super().__init__(fields=[duration_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''


class PhaseForm(Form):
    def __init__(self,
                 default_reached_temp: float|None,
                 default_duration: float|None,
                 default_is_room_temp: bool|None,
                 default_phase_type: phase_types | None,
                 default_stoichio: str|None,
                 end_step: AnnealingStep|None,
                 phase_idx: int,
                 key: str, ):
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
        if self.is_vacuum and self.atmosphere:
            return False, ('Annealing atmosphere is vacuum but a stoichiometry '
                           'has been provided.')
        if not self.is_vacuum and not self.atmosphere:
            return False, 'Missing atmosphere stoichiometry (or check vacuum).'
        return True, ''

    def get_stoichio(self, annealing_step: AnnealingStep) \
            -> list[StoichioElement]:
        if not self.atmosphere:
            return []
        return StoichioElement.from_str(
            formula=self.atmosphere,
            fk_field=StoichioElement.annealing_step,
            parent=annealing_step,
        )


class PhaseListForm(Form):
    def __init__(self, default_annealing: Annealing|None):
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

            if default_annealing is not None:
                db_steps = default_annealing.steps
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

                    if db_phase_start.is_plateau(db_phase_end):
                        default_step_type = phase_types.PLATEAU
                    else:
                        default_step_type = phase_types.RAMP

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
    def __init__(self, default_annealing: Annealing|None):
        intro_form = AnnealingIntroForm(default_annealing)
        st.divider()
        phase_list_form = PhaseListForm(default_annealing)

        self.intro_form = intro_form
        self.phase_list_form = phase_list_form

        super().__init__(fields=[], sub_forms=[intro_form, phase_list_form])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def to_annealing(self, film_modif: FilmModification) -> Annealing:
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
