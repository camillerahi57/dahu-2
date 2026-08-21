import streamlit as st

from components.forms.base_classes import Field, FieldType as Ft, UnitField
from logic.constants import CookieKeys as Ck, SessionKeys as Sk
from logic.db_enums import SputteringSystem, FilmLayerFunction, \
    MagnetronSputteringGenerator, MagnetronMachineModel
from logic.utils import is_valid_email_address
from logic.lab_modelization.db_models import (Library, Film, Target, Patch,
                                              Substrate)
from logic.units import ur


class LibLabelField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill, key):
        return st.text_input("Library Label", value=prefill, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        if not input_:
            return False, "Please enter a label."
        is_taken = input_ in Library.already_taken_names()
        is_default = input_ == self.prefill
        if is_taken and not is_default:
            return False, "This label is already taken."
        return True, ''


class FilmLabelField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill, key):
        return st.text_input("Film label as written on the sample",
                             value=prefill, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == '':
            return False, "Please enter a label."
        is_taken = input_ in Film.already_taken_names()
        is_default = input_ == self.prefill
        if is_taken and not is_default:
            return False, (
                "This label is already used. A library corresponding to this "
                "sample might have already been created.")
        return True, ''


class MagnetronModelField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill: str, key):
        options = [m.value for m in MagnetronMachineModel]
        if not prefill:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Magnetron Machine Model", options=options,
                            key=key, index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class CommentField(Field):
    type = Ft.OPTIONAL
    
    def _streamlit_input(self, prefill, key):
        return st.text_area("Comment", value=prefill, width=600)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class LayerCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        return st.number_input("**Number of layers:**", min_value=0,
                               value=prefill, step=1, width=200)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'The number of layers must be greater than zero.'
        return True, ''


class MadeOnField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill, key):
        return st.date_input("Made on", value=prefill,
                             max_value='today')

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class SputteringSystemField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        options = [s.value for s in SputteringSystem]
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Sputtering system", options=options,
                            index=index, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class MadeByField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill, key):
        if prefill == '':
            prefill = st.session_state.get(Ck.LAST_EMAIL_USED, '')
        return st.text_input("Made by (email address)", value=prefill,
                             width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        if not is_valid_email_address(input_):
            return False, 'Please enter a valid email address.'
        return True, ''


class SubstrateField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill: str, key):
        options = Substrate.already_taken_names()
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Substrate", options=options,
                            index=index, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == '' or input_ is None:
            return False, 'Please select a substrate.'
        return True, ''


class TargetCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: int, key):
        return st.number_input("Number of different target used:", min_value=0,
                               value=prefill, step=1, width=200)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'The number of layers must be greater than zero.'
        return True, ''



class TargetField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill: str, key):
        options = Target.already_taken_names()
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Target", options=options, index=index,
                            key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if not input_:
            return False, 'Please enter select a target.'
        return True, ''


class TargetChoiceField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        options = st.session_state[Sk.SELECTED_TARGETS]
        if not prefill:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Target", options=options, index=index,
                            key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if not input_:
            return False, 'Please enter select a target.'
        return True, ''


class NominalStoichioField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill, key):
        return st.text_input("Nominal stoichiometry", value=prefill,
                             key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return Patch.is_valid_formula(input_)


class FilmLayerFunctionField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill: str, key):
        options = [f.value for f in FilmLayerFunction]
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Layer function", options=options,
                            index=index, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == '' or input_ is None:
            return False, 'Please select an option.'
        return True, ''


class DepositTempField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.celsius
    
    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Deposit temperature ({self.ui_unit:~P})",
                               min_value=0., value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Deposit temperature must be strictly positive.'
        return True, ''


class DepositDurationField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.second
    
    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Deposit duration ({self.ui_unit})",
                               min_value=0., value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Deposit duration must be strictly positive.'
        return True, ''


class NominalThicknessField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.nm

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Nominal thickness ({self.ui_unit})",
                               min_value=0., key=key, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Nominal thickness must be strictly positive.'
        return True, ''


class ShadowMaskField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill: str, key):
        return st.text_area("Shadow mask description", value=prefill,
                            key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class DepositPowerField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.watt
    
    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Deposit power ({self.ui_unit})",
                               min_value=0., key=key, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Deposit power must be strictly positive.'
        return True, ''


class IsCoSputteringField(Field):
    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill: bool, key):
        return st.checkbox("Add co-sputtering", value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class DepositDistanceField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.mm
    
    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Deposit distance ({self.ui_unit})",
                               min_value=0., key=key, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == 0:
            return False, 'Deposit distance must be strictly positive.'
        return True, ''


class DepositAngleField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.degrees

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Deposit angle ({self.ui_unit})",
                               value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class MagnetronGeneratorField(Field):
    type = Ft.ADVISED
    
    def _streamlit_input(self, prefill: str, key):
        options = [gen.value for gen in MagnetronSputteringGenerator]
        if not prefill:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Sputtering generator", options=options,
                            key=key, index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class HasActiveCoolingField(Field):
    type = Ft.ADVISED
    
    def _streamlit_input(self, prefill, key):
        return st.checkbox("Has active cooling", value=prefill,
                           key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ == '' or input_ is None:
            return False, 'Please select an option.'
        return True, ''


class RotationSpeedField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.rpm

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Rotation ({self.ui_unit})",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        return True, ''


class FilamentCurrentStartField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(
            f"Filament current at the beginning ({self.ui_unit})",
            key=key, value=prefill, min_value=0.
        )

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Filament current must be strictly positive.'
        return True, ''


class FilamentCurrentEndField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(
            f"Filament current at the end ({self.ui_unit})",
            key=key, value=prefill, min_value=0.
        )

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Filament current must be strictly positive.'
        return True, ''


class AnodeCurrentField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Anode current ({self.ui_unit})",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Anode current must be strictly positive.'
        return True, ''


class AnodeVoltageField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.volt

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Anode voltage ({self.ui_unit}",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Anode voltage must be strictly positive.'
        return True, ''


class CathodeCurrentField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Cathode current ({self.ui_unit})",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Cathode current must be strictly positive.'
        return True, ''


class CathodeVoltageField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.volt

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Cathode voltage ({self.ui_unit})",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Cathode voltage must be strictly positive.'
        return True, ''


class DepositRateField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.nm / ur.second

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Deposit rate ({self.ui_unit})",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Deposit rate must be strictly positive.'
        return True, ''


class ArgonFlowField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.m**3 / ur.s

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Argon flow ({self.ui_unit})",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Argon flow must be strictly positive.'
        return True, ''


class NitrogenFlowField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.m**3 / ur.s
    ui_unit_alias = 'SCCM'

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Nitrogen flow ({self.ui_unit_alias})",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Nitrogen flow must be strictly positive.'
        return True, ''


class PressureField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.Pa

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(f"Pressure ({self.ui_unit})",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Pressure must be strictly positive.'
        return True, ''


class PresputteringThicknessField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.nm

    def _streamlit_input(self, prefill: float, key):
        return st.number_input(
            f"Presputtering thickness ({self.ui_unit}), if any:",
                value=prefill, key=key, min_value=0.)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ <= 0:
            return False, 'Presputtering thickness must be strictly positive.'
        return True, ''


class ConfirmOrderField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: float, key):
        return st.checkbox("The layers are in the right order "
                           "(bottom to top of the film).")

    def _validate(self, input_) -> tuple[bool, str]:
        if not input_:
            return False, "Please make sure the layers are in the right order."
        return True, ''