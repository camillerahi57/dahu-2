from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import streamlit as st

from logic.constants import PATTERN_IMAGE_PATH, SessionKeys as Sk
from logic.db_enums import FilmModifType
from logic.db_schema import FilmModification, Annealing, IonBeamEtching, \
    WetEtching, Patterning, PlasmaConstituent, AcidConstituent, db
from logic.form_fields.new_film_modif import MadeByField, MadeOnField, \
    ModifTypeField, MadeAfterField, TemperatureField, DurationField, \
    PressureField, FurnaceField, FlowField, AngleField, \
    RotationField, PowerField, PatternField, ProportionField, \
    NumberOfConstituentsField, PlasmaFormulaField, AcidFormulaField
from logic.form_fields.shared import DialogData, FormField


@dataclass
class ModifData(DialogData):
    made_on: datetime
    modif_number: int
    made_by_email: str
    modif_type: FilmModifType
    type_data: (AnnealingForm | IonBeamEtchingForm | WetEtchingForm |
                PatterningForm)

    @classmethod
    @st.dialog("New Film Modification")
    def form(cls):
        made_by_fld = MadeByField.input()
        date_fld = MadeOnField.input()
        modif_type_fld = ModifTypeField.input()
        made_after_fld = MadeAfterField.input()
        fields_ = [made_by_fld, date_fld, modif_type_fld, made_after_fld]

        modif_type = modif_type_fld.value

        if modif_type is not None:
            if modif_type == FilmModifType.ANNEALING:
                type_data = AnnealingForm(fields_)
            elif modif_type == FilmModifType.ION_BEAM_ETCHING:
                type_data = IonBeamEtchingForm(fields_)
            elif modif_type == FilmModifType.WET_ETCHING:
                type_data = WetEtchingForm(fields_)
            elif modif_type == FilmModifType.PATTERNING:
                type_data = PatterningForm(fields_)
            else:
                raise RuntimeError(f'Unknown modification type: {modif_type}')

            if st.button('OK', disabled=not all([f.is_valid for f in fields_])):
                sess = st.session_state
                previous_modif_nb, _ = made_after_fld.value
                with db.atomic():
                    form_data = cls(
                        all_form_fields=fields_,
                        made_on=date_fld.value,
                        modif_number=previous_modif_nb + 1,
                        made_by_email=made_by_fld.value,
                        modif_type=modif_type_fld.value,
                        type_data=type_data,
                    )
                    new_film_modif = FilmModification.new(
                        made_on=form_data.made_on,
                        modif_number=form_data.modif_number,
                        made_by_email=form_data.made_by_email,
                        modif_type=form_data.modif_type,
                        film=sess[Sk.CURRENT_FILM],
                    )
                    new_film_modif.save()
                    if isinstance(type_data, AnnealingForm):
                        annealing = Annealing.new(
                            temperature=type_data.temperature,
                            duration=type_data.duration,
                            pressure=type_data.pressure,
                            furnace=type_data.furnace,
                            film_modif=new_film_modif
                        )
                        annealing.save()
                    elif isinstance(type_data, IonBeamEtchingForm):
                        ion_etching = IonBeamEtching.new(
                            duration=type_data.duration,
                            flow=type_data.flow,
                            incidence_angle=type_data.angle,
                            rotation=type_data.rotation,
                            power=type_data.power,
                            pressure=type_data.pressure,
                            film_modif=new_film_modif,
                        )
                        ion_etching.save()
                        proportion_sum = sum(
                            const.proportion
                            for const in type_data.constituents)
                        for const_data in type_data.constituents:
                            constituent = PlasmaConstituent.new(
                                proportion=const_data.proportion/proportion_sum,
                                formula=const_data.formula,
                                etching=ion_etching
                            )
                            constituent.save()
                    elif isinstance(type_data, WetEtchingForm):
                        wet_etching = WetEtching.new(
                            duration=type_data.duration,
                            temperature=type_data.temp,
                            film_modif=new_film_modif,
                        )
                        wet_etching.save()
                        proportion_sum = sum(
                            const.proportion
                            for const in type_data.constituents
                        )
                        for const_data in type_data.constituents:
                            constituent = AcidConstituent.new(
                                proportion=const_data.proportion/proportion_sum,
                                formula=const_data.formula,
                                etching=wet_etching
                            )
                            constituent.save()
                    elif isinstance(type_data, PatterningForm):
                        patterning = Patterning.new(
                            diagram_file_name=type_data.pattern,
                            film_modif=new_film_modif,
                        )
                        patterning.save()
                    else:
                        raise RuntimeError(f'Unknown modification type: '
                                           f'{modif_type}')

                form_data.clear_all_fields()
                st.rerun()


class AnnealingForm:
    def __init__(self, fields: list[FormField]):
        temp_fld = TemperatureField.input()
        duration_fld = DurationField.input()
        pressure_fld = PressureField.input()
        furnace_fld = FurnaceField.input()

        fields += [temp_fld, duration_fld, pressure_fld, furnace_fld]

        self.temperature = temp_fld.value
        self.duration = duration_fld.value
        self.pressure = pressure_fld.value
        self.furnace = furnace_fld.value


@dataclass
class ConstituentData:
    formula: str
    proportion: float


class IonBeamEtchingForm:
    def __init__(self, fields: list[FormField]):
        duration_fld = DurationField.input()
        flow_fld = FlowField.input()
        angle_fld = AngleField.input()
        rotation_fld = RotationField.input()
        power_fld = PowerField.input()
        pressure_fld = PressureField.input()

        fields += [duration_fld, flow_fld, angle_fld,
                   rotation_fld, power_fld, pressure_fld]

        st.subheader('Plasma constituents:')
        constituent_nb_fld = NumberOfConstituentsField.input()

        constituents = []
        for i in range(constituent_nb_fld.value):
            with st.container(horizontal=True, vertical_alignment='center'):
                formula_fld = PlasmaFormulaField.input(key=f'formula_{i}')
                proportion_fld = ProportionField.input(key=f'proportion_{i}')
                data = ConstituentData(
                    formula=formula_fld.value,
                    proportion=proportion_fld.value,
                )
                constituents.append(data)
                fields += [formula_fld, proportion_fld]

        self.duration = duration_fld.value
        self.flow = flow_fld.value
        self.angle = angle_fld.value
        self.rotation = rotation_fld.value
        self.power = power_fld.value
        self.pressure = pressure_fld.value
        self.constituents = constituents


class WetEtchingForm:
    def __init__(self, fields: list[FormField]):
        duration_fld = DurationField.input()
        temp_fld = TemperatureField.input()

        fields += [duration_fld, temp_fld]

        st.subheader('Acid constituents:')
        constituent_nb_fld = NumberOfConstituentsField.input()

        constituents = []
        for i in range(constituent_nb_fld.value):
            with st.container(horizontal=True, vertical_alignment='center'):
                formula_fld = AcidFormulaField.input(key=f'formula_{i}')
                proportion_fld = ProportionField.input(key=f'proportion_{i}')
                data = ConstituentData(
                    formula=formula_fld.value,
                    proportion=proportion_fld.value,
                )
                constituents.append(data)
                fields += [formula_fld, proportion_fld]

        self.duration = duration_fld.value
        self.temp = temp_fld.value
        self.constituents = constituents


class PatterningForm:
    def __init__(self, fields: list[FormField]):
        pattern_fld = PatternField.input()

        if pattern_fld.value != '':
            pattern_path = Path(PATTERN_IMAGE_PATH) / pattern_fld.value
            st.image(pattern_path)
        fields += [pattern_fld]
        self.pattern = pattern_fld.value

