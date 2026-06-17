import streamlit as st

from components.forms.shared2 import Field, FieldType as Ft, UnitField
from logic.constants import CookieKeys as Ck, SessionKeys as Sk
from logic.db_enums import SputteringSystem, FilmLayerFunction, \
    MagnetronSputteringGenerator, MagnetronMachineModel
from logic.functions import is_valid_email_address
from logic.lab_modelization.db_models import (Library, Film, Target, Patch,
                                              Substrate)
from logic.units import ur


class LibLabelField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill=''):
        return st.text_input("Library Label", value=prefill, width=300)

    def _validate(self) -> tuple[bool, str]:
        if self._input in Library.already_taken_names():
            return False, "This label is already taken."
        if self._input == '':
            return False, "Please enter a label."
        return True, ''


class FilmLabelField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill=''):
        return st.text_input("Film label as written on the sample",
                             value=prefill, width=300)

    def _validate(self) -> tuple[bool, str]:
        if self._input in Film.already_taken_names():
            return False, (
                "This label is already used. A library corresponding to this "
                "sample might have already been created.")
        if self._input == '':
            return False, "Please enter a label."
        return True, ''


class MagnetronModelField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill: str = ''):
        options = [m.value for m in MagnetronMachineModel]
        if prefill in {'', None}:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Magnetron Machine Model", options=options,
                            key=self.key, index=index)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class CommentField(Field):
    type = Ft.OPTIONAL
    
    def _streamlit_input(self, prefill=''):
        return st.text_area("Comment", value=prefill, width=600)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class LayerCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill=0):
        return st.number_input("**Number of layers:**", min_value=0,
                               value=prefill, step=1, width=200)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'The number of layers must be greater than zero.'
        return True, ''


class MadeOnField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill=None):
        return st.date_input("Made on", value=prefill,
                             max_value='today')

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class SputteringSystemField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill=None):
        options = [s.value for s in SputteringSystem]
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Sputtering system", options=options,
                            index=index, key=self.key)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class MadeByField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill=''):
        if prefill == '':
            prefill = st.session_state.get(Ck.LAST_EMAIL_USED, '')
        return st.text_input("Made by (email address)", value=prefill,
                             width=300)

    def _validate(self) -> tuple[bool, str]:
        if not is_valid_email_address(self._input):
            return False, 'Please enter a valid email address.'
        return True, ''

#
# class UploadField(Field):
#     type = Ft.OPTIONAL
#
#     def _streamlit_input(self, prefill=None):
#         return st.file_uploader("Upload any file related to this library.",
#                                 accept_multiple_files=True)
#
#     def _validate(self) -> tuple[bool, str]:
#         if self.value is None:
#             return False, 'Please upload a zip file.'
#         else:
#             return True, ''


class SubstrateField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill: str = None):
        options = Substrate.already_taken_names()
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Substrate", options=options,
                            index=index, width=300)

    def _validate(self) -> tuple[bool, str]:
        if self._input == '' or self._input is None:
            return False, 'Please select a substrate.'
        return True, ''


class TargetCountField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: int = 0):
        return st.number_input("Number of different target used:", min_value=0,
                               value=prefill, step=1, width=200)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'The number of layers must be greater than zero.'
        return True, ''



class AllTargetField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill: str = None):
        options = Target.already_taken_names()
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Target", options=options, index=index,
                            key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input in {'', None}:
            return False, 'Please enter select a target.'
        return True, ''


class TargetChoiceField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str = None):
        options = st.session_state[Sk.SELECTED_TARGETS]
        if prefill in {None, ''}:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Target", options=options, index=index,
                            key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input in {'', None}:
            return False, 'Please enter select a target.'
        return True, ''


class NominalStoichioField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill=''):
        return st.text_input("Nominal stoichiometry", value=prefill,
                             key=self.key)

    def _validate(self) -> tuple[bool, str]:
        return Patch.is_valid_formula(self._input)


class FilmLayerFunctionField(Field):
    type = Ft.MANDATORY
    
    def _streamlit_input(self, prefill: str = None):
        options = [f.value for f in FilmLayerFunction]
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Layer function", options=options,
                            index=index, key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input == '' or self._input is None:
            return False, 'Please select an option.'
        return True, ''


class DepositTempField(Field):
    type = Ft.ADVISED
    
    def _streamlit_input(self, prefill: float = 300.):
        return st.number_input("Deposit temperature (Kelvin)",
                               min_value=0., value=prefill, key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Deposit temperature must be strictly positive.'
        return True, ''


class DepositDurationField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.second
    
    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Deposit duration", min_value=0.,
                               value=prefill, key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Deposit duration must be strictly positive.'
        return True, ''


class NominalThicknessField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Nominal thickness", min_value=0.,
                               key=self.key, value=prefill)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Nominal thickness must be strictly positive.'
        return True, ''


class ShadowMaskField(Field):
    type = Ft.ADVISED

    def _streamlit_input(self, prefill: str = None):
        return st.text_area("Shadow mask", value=prefill, key=self.key)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class DepositPowerField(Field):
    type = Ft.ADVISED
    
    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Deposit power", min_value=0.,
                               key=self.key, value=prefill)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Deposit power must be strictly positive.'
        return True, ''


class DepositDistanceField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.mm
    
    def _streamlit_input(self, prefill: float = 100.):
        return st.number_input("Deposit distance (mm)", min_value=0.,
                               key=self.key, value=prefill)

    def _validate(self) -> tuple[bool, str]:
        if self._input == 0:
            return False, 'Deposit distance must be strictly positive.'
        return True, ''


class DepositAngleField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.degrees

    def _streamlit_input(self, prefill: float = 0.):
        return st.number_input("Deposit angle (degrees)", value=prefill,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class MagnetronGeneratorField(Field):
    type = Ft.ADVISED
    
    def _streamlit_input(self, prefill: str = None):
        options = [gen.value for gen in MagnetronSputteringGenerator]
        if prefill in {None, ''}:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Sputtering generator", options=options,
                            key=self.key, index=index)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class HasActiveCoolingField(Field):
    type = Ft.ADVISED
    
    def _streamlit_input(self, prefill=True):
        return st.checkbox("Has active cooling", value=prefill,
                           key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input == '' or self._input is None:
            return False, 'Please select an option.'
        return True, ''


class RotationSpeedField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.rpm

    def _streamlit_input(self, prefill: float = 0.):
        return st.number_input("Rotation", value=prefill, min_value=0.,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        return True, ''


class FilamentCurrentStartField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Filament current at the beginning",
                               key=self.key, value=prefill, min_value=0.)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Filament current must be strictly positive.'
        return True, ''


class FilamentCurrentEndField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Filament current at the end",
                               key=self.key, value=prefill, min_value=0.)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Filament current must be strictly positive.'
        return True, ''


class AnodeCurrentField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Anode current", value=prefill, min_value=0.,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Anode current must be strictly positive.'
        return True, ''


class AnodeVoltageField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.volt

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Anode voltage", value=prefill, min_value=0.,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Anode voltage must be strictly positive.'
        return True, ''


class CathodeCurrentField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Cathode current", value=prefill, min_value=0.,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Cathode current must be strictly positive.'
        return True, ''


class CathodeVoltageField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.volt

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Cathode voltage", value=prefill, min_value=0.,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Cathode voltage must be strictly positive.'
        return True, ''


class DepositRateField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.nm / ur.second

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Deposit rate", value=prefill, min_value=0.,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Deposit rate must be strictly positive.'
        return True, ''


class ArgonFlowField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.m**3 / ur.s

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Argon flow", value=prefill, min_value=0.,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Argon flow must be strictly positive.'
        return True, ''


class NitrogenFlowField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.m**3 / ur.s

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Nitrogen flow", value=prefill, min_value=0.,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Nitrogen flow must be strictly positive.'
        return True, ''


class PressureField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.Pa

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Pressure", value=prefill, min_value=0.,
                               key=self.key)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Pressure must be strictly positive.'
        return True, ''


class PresputteringThicknessField(UnitField):
    type = Ft.ADVISED
    ui_unit = ur.nm

    def _streamlit_input(self, prefill: float = None):
        return st.number_input("Presputtering thickness", value=prefill,
                               key=self.key, min_value=0.)

    def _validate(self) -> tuple[bool, str]:
        if self._input <= 0:
            return False, 'Presputtering thickness must be strictly positive.'
        return True, ''


class ConfirmOrderField(Field):
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: float = False):
        return st.checkbox("The layers are in the right order.")

    def _validate(self) -> tuple[bool, str]:
        if not self._input:
            return False, "Please make sure the layers are in the right order."
        return True, ''