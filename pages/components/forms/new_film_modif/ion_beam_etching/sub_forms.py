import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.fields import IonDurationField, FlowField,\
    AngleField, RotationField, PowerField, PressureField, HasPatternField, \
    ConstituentCountField, PlasmaFormulaField, \
    PlasmaProportionField
from components.forms.new_film_modif.shared import PatternDiagramForm
from logic.lab_modelization.db_models import IonBeamEtching, \
    FilmModification, PlasmaConstituent


class ConstituentForm(Form):
    def __init__(self, stoichio_from_db: str | None,
                 proportion_from_db: float | None):
        with st.container(horizontal=True):
            formula_fld = PlasmaFormulaField(
                form_default='',
                db_default=stoichio_from_db
            )
            proportion_fld = PlasmaProportionField(
                form_default=None,
                db_default=proportion_from_db,
            )

        self.formula: str = formula_fld.value
        self.proportion: float = proportion_fld.value

        super().__init__(fields=[formula_fld, proportion_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''


class ConstituentListForm(Form):
    def __init__(self, default_etching: IonBeamEtching|None):
        st.title('Plasma Constituents')
        count_fld = ConstituentCountField(
            form_default=1,
            db_default=None if not default_etching
                else len(default_etching.constituents)
        )
        constituent_forms: list[ConstituentForm] = []
        for i in range(count_fld.value):
            if not default_etching:
                db_formula, db_proportion = None, None
            else:
                try:
                    db_constituent = default_etching.constituents[i]
                    db_formula = db_constituent.stoichio_str
                    db_proportion = db_constituent.proportion
                except IndexError:
                    db_formula, db_proportion = None, None
            form = ConstituentForm(db_formula, db_proportion)
            constituent_forms.append(form)

        self.formula_list = [(f.formula, f.proportion)
                             for f in constituent_forms]
        super().__init__(fields=[count_fld], sub_forms=constituent_forms)

    def _is_coherent(self) -> tuple[bool, str]:
        # Making sure all formulas are different:
        formula_set = set(self.formula_list)
        if len(formula_set) != len(self.formula_list):
            return False, 'Some formulas are identical.'
        return True, ''

    def to_constituents(self, etching: IonBeamEtching) \
            -> list[PlasmaConstituent]:
        if not self.is_valid:
            raise PausePageRun
        proportion_sum = sum(prop for _, prop in self.formula_list)
        return [
            PlasmaConstituent.from_stoichio(
                formula,
                proportion / proportion_sum,
                etching)
            for formula, proportion in self.formula_list
        ]


class IonEtchingForm(Form):
    def __init__(self, default_etching: IonBeamEtching|None):
        with st.container(horizontal=True):
            duration_fld = IonDurationField(
                form_default=None,
                db_default=None if not default_etching
                    else default_etching.duration,
            )
            flow_fld = FlowField(
                form_default=None,
                db_default=None if not default_etching
                    else default_etching.flow,
            )
            angle_fld = AngleField(
                form_default=None,
                db_default=None if not default_etching
                    else default_etching.incidence_angle
            )
            rotation_fld = RotationField(
                form_default=None,
                db_default=None if not default_etching
                    else default_etching.rotation
            )
            power_fld = PowerField(
                form_default=None,
                db_default=None if not default_etching
                    else default_etching.power
            )
            pressure_fld = PressureField(
                form_default=None,
                db_default=None if not default_etching
                    else default_etching.pressure
            )
        st.subheader("Pattern")
        has_pattern_fld = HasPatternField(
            form_default=None,
            db_default=None if not default_etching
                else default_etching.has_a_pattern
        )
        if not has_pattern_fld.is_filled:
            raise PausePageRun

        has_pattern = has_pattern_fld.value == HasPatternField.Option.YES
        if has_pattern:
            if default_etching and default_etching.patterns:
                default_diagram = default_etching.patterns[0]
            else:
                default_diagram = None
            pattern_form = PatternDiagramForm(default_diagram)
        else:
            pattern_form = None

        st.divider()
        constituent_form = ConstituentListForm(default_etching)

        self.duration = duration_fld.value
        self.flow = flow_fld.value
        self.incidence_angle = angle_fld.value
        self.rotation = rotation_fld.value
        self.power = power_fld.value
        self.pressure = pressure_fld.value
        self.has_pattern = has_pattern
        self.pattern_form = pattern_form
        self.constituent_form = constituent_form
        super().__init__(
            fields=[duration_fld, flow_fld, angle_fld, rotation_fld, power_fld,
                    pressure_fld, has_pattern_fld],
            sub_forms=[constituent_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        # User can indicate that there is a pattern without providing it.
        return True, ''

    def to_ion_etching(self, film_modif: FilmModification) \
            -> IonBeamEtching:
        """Return an ion etching object with pattern image bytes."""
        if not self.is_valid:
            raise PausePageRun

        ion_etching = IonBeamEtching(
            duration=self.duration,
            flow=self.flow,
            incidence_angle=self.incidence_angle,
            rotation=self.rotation,
            power=self.power,
            pressure=self.pressure,
            has_a_pattern=self.has_pattern,
            film_modif=film_modif,
        )

        pattern_form = self.pattern_form
        pattern = pattern_form.to_ion_etching_pattern(ion_etching) \
            if pattern_form else None
        constituents = self.constituent_form.to_constituents(ion_etching)

        if pattern:
            ion_etching.patterns = [pattern]
        ion_etching.constituents = constituents

        return ion_etching