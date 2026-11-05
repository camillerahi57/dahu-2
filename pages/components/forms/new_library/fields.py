"""Form fields of the "new library" form and of the library edit pages.

Each class draws one Streamlit widget and validates its input (see
`Field` in `components/forms/base_classes.py`). They are assembled into
forms in `sub_forms.py` of this package, which the "new library",
"edit library", "edit film" and "edit film layers" pages use.

Some classes are also used outside forms, only for their unit: the
models' `title_db_value_input_fields` (in `db_models.py`),
`logic/table_columns.py` and `pages/inspect_library.py` call their
`db_to_ui_str()` to show DB values in UI units.

Unit fields (`UnitField`) take input in their `ui_unit`; the DB stores
SI base units (see `logic/units.py`). Each class docstring gives both.

Fields that don't pass `key` to their widget let Streamlit build the
widget key (the name Streamlit uses to recognize a widget from one
rerun to the next) from the label, so they can appear only once per
page.
"""

import streamlit as st

from components.forms.base_classes import Field, FieldType as Ft, UnitField
from logic.constants import SessionKeys as Sk
from logic.lab_modelization.db_enums import (
    SputteringSystem, FilmLayerFunction,
    MagnetronSputteringGenerator, MagnetronMachineModel)
from logic.lab_modelization.db_models import (Library, Film, Target, Patch,
                                              Substrate)
from logic.units import ur
from logic.utils import is_valid_email_address, all_email_addresses


class LibLabelField(Field):
    """Unique label (name) of the library (`Library.label`)."""
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw a text input. See `Field._streamlit_input`."""
        return st.text_input("Library Label", value=prefill, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a non-empty label not used by another library.

        The prefilled label is allowed, so that an edited library can
        keep its own label. See `Field._validate`.
        """
        if not input_:
            return False, "Please enter a label."
        is_taken = input_ in Library.already_taken_names()
        is_default = input_ == self.prefill
        if is_taken and not is_default:
            return False, "This label is already taken."
        return True, ''


class FilmLabelField(Field):
    """Unique label of the film, as written on the sample
    (`Film.label`)."""
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw a text input. See `Field._streamlit_input`."""
        return st.text_input("Film label as written on the sample",
                             value=prefill, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a non-empty label not used by another film.

        The prefilled label is allowed, so that an edited film can keep
        its own label. A taken label usually means that a library was
        already created for this sample. See `Field._validate`.
        """
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
    """Magnetron sputtering machine used, a `MagnetronMachineModel`
    value (`MagnetronSputtering.machine_model`)."""
    type = Ft.ADVISED

    def _streamlit_input(self, prefill: str, key):
        """Draw a selectbox of the enum values, empty when no prefill.

        See `Field._streamlit_input`.
        """
        options = [m.value for m in MagnetronMachineModel]
        if not prefill:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Magnetron Machine Model", options=options,
                            key=key, index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any choice. See `Field._validate`."""
        return True, ''


class CommentField(Field):
    """Free-text comment on the library (`Library.comment`)."""
    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key):
        """Draw a text area. See `Field._streamlit_input`."""
        return st.text_area("Comment", value=prefill, width=600)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any text. See `Field._validate`."""
        return True, ''


class LayerCountField(Field):
    """Number of layers of the film; decides how many `LayerForm`s are
    drawn."""
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw an integer input (minimum 0, step 1).

        See `Field._streamlit_input`.
        """
        return st.number_input("**Number of layers:**", min_value=0,
                               value=prefill, step=1, width=200)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require at least one layer.

        `0` counts as filled (see `Field.is_filled`), so it reaches this
        check and is refused. See `Field._validate`.
        """
        if input_ <= 0:
            return False, 'The number of layers must be greater than zero.'
        return True, ''


class MadeOnField(Field):
    """Deposition date of the film (`Film.made_on`)."""
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw a date picker that refuses future dates.

        With a None prefill the picker starts empty. See
        `Field._streamlit_input`.
        """
        return st.date_input("Made on", value=prefill,
                             max_value='today')

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any date. See `Field._validate`."""
        return True, ''


class SputteringSystemField(Field):
    """Sputtering system used for a layer, a `SputteringSystem` value
    (`FilmLayer.sputtering_system`).

    `LayerForm` reads it to decide whether to draw `MagnetronForm` or
    `TriodeForm`.
    """
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw a selectbox of the enum values, empty when no prefill.

        See `Field._streamlit_input`.
        """
        options = [s.value for s in SputteringSystem]
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Sputtering system", options=options,
                            index=index, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any choice. See `Field._validate`."""
        return True, ''


class MadeByField(Field):
    """Email of the person who made the film (`Film.made_by_email`)."""
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw a selectbox of known emails that also accepts a new one.

        See `Field._streamlit_input`.
        """
        options = all_email_addresses
        index = options.index(prefill) if prefill in options else None
        return st.selectbox(
            "Made by (email address)",
            options=options, index=index, accept_new_options=True, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a valid email address.

        Side effect: a valid address is saved in the `LAST_EMAIL_USED`
        cookie (see `is_valid_email_address`). See `Field._validate`.
        """
        if not is_valid_email_address(input_):
            return False, 'Please enter a valid email address.'
        return True, ''


class SubstrateField(Field):
    """Label of the substrate the film was deposited on
    (`Film.substrate`)."""
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        """Draw a selectbox of the substrate labels in the DB.

        See `Field._streamlit_input`.
        """
        options = Substrate.already_taken_names()
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Substrate", options=options,
                            index=index, width=300)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a chosen substrate. See `Field._validate`."""
        if input_ == '' or input_ is None:
            return False, 'Please select a substrate.'
        return True, ''


class TargetCountField(Field):
    """Number of different targets used for the film; decides how many
    `TargetField`s `TargetListForm` draws."""
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: int, key):
        """Draw an integer input (minimum 0, step 1).

        See `Field._streamlit_input`.
        """
        return st.number_input("Number of different targets used:", min_value=0,
                               value=prefill, step=1, width=200)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require at least one target. See `Field._validate`."""
        if input_ <= 0:
            # TODO "number of layers" instead of "number of targets".
            return False, 'The number of layers must be greater than zero.'
        return True, ''



class TargetField(Field):
    """One target used for the film, chosen among all targets in the DB.

    The chosen labels are offered by `TargetChoiceField` in each layer.
    """
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        """Draw a selectbox of the target labels in the DB.

        See `Field._streamlit_input`.
        """
        options = Target.already_taken_names()
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Target", options=options, index=index,
                            key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a chosen target. See `Field._validate`."""
        if not input_:
            # TODO typo.
            return False, 'Please enter select a target.'
        return True, ''


class TargetChoiceField(Field):
    """Target used to deposit one layer, chosen among the film's targets.

    The options are the labels chosen in `TargetListForm`, read from the
    session state (`st.session_state`, a dictionary Streamlit keeps for
    each browser tab across reruns) under `SessionKeys.SELECTED_TARGETS`.
    `TargetListForm` must therefore be drawn earlier on the page.
    """
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        """Draw a selectbox of the film's selected targets.

        See `Field._streamlit_input`.
        """
        # TODO `TargetChoiceField`
        #   calls `options.index(prefill)`. On the "edit film layers" page, if the
        #   user removes or changes in `TargetListForm` a target that a layer
        #   uses, the prefilled label is no longer in the options and this raises
        #   `ValueError`. The same `index()` pattern in the other selectbox
        #   fields fails if the prefilled DB value is no longer an option.
        options = st.session_state[Sk.SELECTED_TARGETS]
        if not prefill:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Target", options=options, index=index,
                            key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a chosen target. See `Field._validate`."""
        if not input_:
            # TODO typo.
            return False, 'Please enter select a target.'
        return True, ''


class NominalStoichioField(Field):
    """Intended chemical formula of a layer, e.g. `'Fe2O3'`
    (`FilmLayer.nominal_stoichio`)."""
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill, key):
        """Draw a text input. See `Field._streamlit_input`."""
        return st.text_input("Nominal stoichiometry", value=prefill,
                             key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a valid formula (`Patch.is_valid_formula`).

        See `Field._validate`.
        """
        return Patch.is_valid_formula(input_)


class FilmLayerFunctionField(Field):
    """Role of a layer, a `FilmLayerFunction` value
    (`FilmLayer.function`)."""
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: str, key):
        """Draw a selectbox of the enum values, empty when no prefill.

        See `Field._streamlit_input`.
        """
        options = [f.value for f in FilmLayerFunction]
        if prefill is None:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Layer function", options=options,
                            index=index, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a chosen option. See `Field._validate`."""
        if input_ == '' or input_ is None:
            return False, 'Please select an option.'
        return True, ''


class DepositTempField(UnitField):
    """Deposition temperature of a layer (`FilmLayer.deposit_temp`).

    UI unit: °C. DB unit: K (Pint converts the offset, not just the
    scale).
    """
    type = Ft.ADVISED
    ui_unit = ur.celsius

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input with a minimum of 0 °C.

        See `Field._streamlit_input`.
        """
        # `~P`: Pint's short, "pretty" unit format, i.e. °C.
        return st.number_input(f"Deposit temperature ({self.ui_unit:~P})",
                               min_value=0., value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a temperature above 0 °C. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Deposit temperature must be strictly positive.'
        return True, ''


class DepositDurationField(UnitField):
    """Deposition duration of a layer (`deposit_duration` of
    `MagnetronSputtering` and `TriodeSputtering`).

    UI unit: s. DB unit: s.
    """
    type = Ft.ADVISED
    ui_unit = ur.second

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Deposit duration (**{self.ui_unit}**)",
                               min_value=0., value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Deposit duration must be strictly positive.'
        return True, ''


class NominalThicknessField(UnitField):
    """Intended thickness of a layer (`FilmLayer.nominal_thickness`).

    UI unit: nm. DB unit: m.
    """
    type = Ft.ADVISED
    ui_unit = ur.nm

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Nominal thickness (**{self.ui_unit}**)",
                               min_value=0., key=key, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Nominal thickness must be strictly positive.'
        return True, ''


class ShadowMaskField(Field):
    """Free-text description of the shadow mask used for a layer
    (`FilmLayer.shadow_mask_description`)."""
    type = Ft.ADVISED

    def _streamlit_input(self, prefill: str, key):
        """Draw a text area. See `Field._streamlit_input`."""
        return st.text_area("Shadow mask description", value=prefill,
                            key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any text. See `Field._validate`."""
        return True, ''


class DepositPowerField(UnitField):
    """Magnetron generator power (`MagnetronSputtering.deposit_power`).

    UI unit: W. DB unit: W.
    """
    type = Ft.ADVISED
    ui_unit = ur.watt

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Deposit power (**{self.ui_unit}**)",
                               min_value=0., key=key, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Deposit power must be strictly positive.'
        return True, ''


class IsCoSputteringField(Field):
    """Whether a layer was co-sputtered from two targets.

    Not stored as such: when checked, `LayerIntroForm` shows a second
    `TargetChoiceField`, and the layer gets two `TargetUse`s.
    """
    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill: bool, key):
        """Draw a checkbox. See `Field._streamlit_input`."""
        return st.checkbox("Add co-sputtering", value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept both states. See `Field._validate`."""
        return True, ''


class DepositDistanceField(UnitField):
    """Target-to-substrate distance
    (`MagnetronSputtering.deposit_distance`).

    UI unit: mm. DB unit: m.
    """
    type = Ft.ADVISED
    ui_unit = ur.mm

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Deposit distance (**{self.ui_unit}**)",
                               min_value=0., key=key, value=prefill)

    def _validate(self, input_) -> tuple[bool, str]:
        """Refuse 0 (the widget already refuses negative values).

        See `Field._validate`.
        """
        if input_ == 0:
            return False, 'Deposit distance must be strictly positive.'
        return True, ''


class DepositAngleField(UnitField):
    """Deposition angle (`MagnetronSputtering.deposit_angle`).

    UI unit: degree. DB unit: rad.
    """
    type = Ft.ADVISED
    ui_unit = ur.degrees

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input with no bounds.

        See `Field._streamlit_input`.
        """
        return st.number_input(f"Deposit angle (**{self.ui_unit}**)",
                               value=prefill, key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any angle. See `Field._validate`."""
        return True, ''


class MagnetronGeneratorField(Field):
    """Magnetron generator used, a `MagnetronSputteringGenerator` value
    (`MagnetronSputtering.generator`)."""
    type = Ft.ADVISED

    def _streamlit_input(self, prefill: str, key):
        """Draw a selectbox of the enum values, empty when no prefill.

        See `Field._streamlit_input`.
        """
        options = [gen.value for gen in MagnetronSputteringGenerator]
        if not prefill:
            index = None
        else:
            index = options.index(prefill)
        return st.selectbox("Sputtering generator", options=options,
                            key=key, index=index)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any choice. See `Field._validate`."""
        return True, ''


class HasActiveCoolingField(Field):
    """Whether the substrate was actively cooled during triode
    sputtering (`TriodeSputtering.has_active_cooling`)."""
    type = Ft.ADVISED

    def _streamlit_input(self, prefill, key):
        """Draw a checkbox. See `Field._streamlit_input`."""
        return st.checkbox("Has active cooling", value=prefill,
                           key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept both states. See `Field._validate`."""
        # A checkbox always returns True or False, so this test never
        # fails.
        if input_ == '' or input_ is None:
            return False, 'Please select an option.'
        return True, ''


class RotationSpeedField(UnitField):
    """Substrate rotation speed during triode sputtering
    (`TriodeSputtering.rotation_speed`).

    UI unit: rpm. DB unit: rad/s.
    """
    type = Ft.ADVISED
    ui_unit = ur.rpm

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Rotation (**{self.ui_unit}**)",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Accept any value, 0 included. See `Field._validate`."""
        return True, ''


class FilamentCurrentStartField(UnitField):
    """Triode filament current at the start of the deposition
    (`TriodeSputtering.filament_current_start`).

    UI unit: A. DB unit: A.
    """
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(
            f"Filament current at the beginning (**{self.ui_unit}**)",
            key=key, value=prefill, min_value=0.
        )

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Filament current must be strictly positive.'
        return True, ''


class FilamentCurrentEndField(UnitField):
    """Triode filament current at the end of the deposition
    (`TriodeSputtering.filament_current_end`).

    UI unit: A. DB unit: A.
    """
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(
            f"Filament current at the end (**{self.ui_unit}**)",
            key=key, value=prefill, min_value=0.
        )

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Filament current must be strictly positive.'
        return True, ''


class AnodeCurrentField(UnitField):
    """Triode anode current (`TriodeSputtering.anode_current`).

    UI unit: A. DB unit: A.
    """
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Anode current (**{self.ui_unit}**)",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Anode current must be strictly positive.'
        return True, ''


class AnodeVoltageField(UnitField):
    """Triode anode voltage (`TriodeSputtering.anode_voltage`).

    UI unit: V. DB unit: V.
    """
    type = Ft.ADVISED
    ui_unit = ur.volt

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Anode voltage (**{self.ui_unit}**)",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Anode voltage must be strictly positive.'
        return True, ''


class CathodeCurrentField(UnitField):
    """Triode cathode current (`TriodeSputtering.cathode_current`).

    UI unit: A. DB unit: A.
    """
    type = Ft.ADVISED
    ui_unit = ur.A

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Cathode current (**{self.ui_unit}**)",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Cathode current must be strictly positive.'
        return True, ''


class CathodeVoltageField(UnitField):
    """Triode cathode voltage (`TriodeSputtering.cathode_voltage`).

    UI unit: V. DB unit: V.
    """
    type = Ft.ADVISED
    ui_unit = ur.volt

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Cathode voltage (**{self.ui_unit}**)",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Cathode voltage must be strictly positive.'
        return True, ''


class DepositRateField(UnitField):
    """Triode deposition rate (`TriodeSputtering.deposit_rate`).

    UI unit: nm/s. DB unit: m/s.
    """
    type = Ft.ADVISED
    ui_unit = ur.nm / ur.second

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Deposit rate (**{self.ui_unit}**)",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Deposit rate must be strictly positive.'
        return True, ''


class ArgonFlowField(UnitField):
    """Argon flow during triode sputtering
    (`TriodeSputtering.argon_flow`).

    UI unit: m³/s. DB unit: m³/s. See the TODO below.
    """
    type = Ft.ADVISED
    # TODO Should it be like NitrogenFlowField? Instead of:
    ui_unit = ur.m**3 / ur.s

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Argon flow (**{self.ui_unit}**)",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Argon flow must be strictly positive.'
        return True, ''


class NitrogenFlowField(UnitField):
    """Nitrogen flow during triode sputtering
    (`TriodeSputtering.nitrogen_flow`).

    The label says SCCM (`ui_unit_alias`), but the conversion uses
    `ui_unit`, m³/s, so the number typed is stored unchanged. See the
    TODO below.
    """
    type = Ft.ADVISED
    # TODO It's cm, not m:
    #  (SCCM means standard cm³ per minute, so the time unit differs
    #  too. Because the alias only changes the label, a value typed as
    #  SCCM is stored as if it were m³/s.)
    ui_unit = ur.m**3 / ur.s
    ui_unit_alias = 'SCCM'

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0) labelled in SCCM.

        See `Field._streamlit_input`.
        """
        return st.number_input(f"Nitrogen flow ({self.ui_unit_alias})",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Nitrogen flow must be strictly positive.'
        return True, ''


class PressureField(UnitField):
    """Pressure during triode sputtering (`TriodeSputtering.pressure`).

    UI unit: Pa. DB unit: Pa.
    """
    type = Ft.ADVISED
    ui_unit = ur.Pa

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(f"Pressure (**{self.ui_unit}**)",
                               value=prefill, min_value=0., key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Pressure must be strictly positive.'
        return True, ''


class PresputteringThicknessField(UnitField):
    """Thickness removed by presputtering, if any
    (`TriodeSputtering.presputtering_thickness`).

    UI unit: nm. DB unit: m.
    """
    type = Ft.ADVISED
    ui_unit = ur.nm

    def _streamlit_input(self, prefill: float, key):
        """Draw a number input (minimum 0). See `Field._streamlit_input`.
        """
        return st.number_input(
            f"Presputtering thickness (**{self.ui_unit}**), if any:",
                value=prefill, key=key, min_value=0.)

    def _validate(self, input_) -> tuple[bool, str]:
        """Require a strictly positive value; leave the field empty for
        no presputtering. See `Field._validate`."""
        if input_ <= 0:
            return False, 'Presputtering thickness must be strictly positive.'
        return True, ''


class ConfirmOrderField(Field):
    """Checkbox the user must tick to confirm the layer order.

    Not stored: it only blocks submission until ticked. Used by the
    "new library" and "edit film layers" root forms.
    """
    type = Ft.MANDATORY

    def _streamlit_input(self, prefill: float, key):
        """Draw an unticked checkbox; `prefill` and `key` are ignored.

        See `Field._streamlit_input`.
        """
        return st.checkbox("The layers are in the right order "
                           "(bottom to top of the film).")

    def _validate(self, input_) -> tuple[bool, str]:
        """Require the box to be ticked. See `Field._validate`.

        An unticked box returns False, which counts as filled (see
        `Field.is_filled`), so it reaches this check.
        """
        if not input_:
            return False, "Please make sure the layers are in the right order."
        return True, ''
