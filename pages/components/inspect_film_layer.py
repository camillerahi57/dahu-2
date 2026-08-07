import streamlit as st

from components.browse import INSPECT_BUTTON_KEY
from components.forms.base_classes import UnitField
from components.forms.new_library.fields import DepositTempField, \
    NominalThicknessField, ShadowMaskField, FilmLayerFunctionField, \
    NominalStoichioField, DepositDistanceField, DepositAngleField, \
    DepositPowerField, DepositDurationField, MagnetronGeneratorField, \
    MagnetronModelField, HasActiveCoolingField, RotationSpeedField, \
    FilamentCurrentStartField, FilamentCurrentEndField, AnodeCurrentField, \
    AnodeVoltageField, CathodeCurrentField, CathodeVoltageField, \
    DepositRateField, ArgonFlowField, NitrogenFlowField, PressureField, \
    PresputteringThicknessField
from components.streamlit_tools import sess, switch_button
from logic.constants import IdType
from logic.db_enums import SputteringSystem
from logic.lab_modelization.db_models import FilmLayer, StoichioElement, \
    MagnetronSputtering, TriodeSputtering, Target, TargetUse
from logic.page_list import pages


@st.dialog(title="Layer info")
def show_film_layer(layers: list[FilmLayer]):
    """Show data about the layer that's been clicked on the layer table in
    the inspect library page."""
    layer = layers[sess[INSPECT_BUTTON_KEY]['row']]
    title_db_value_input_fields: list[tuple[str, float, type[UnitField]]] = [
        # Tuple of a title, the value from the DB, and the UI field it's
        # been entered through (because we want to show the value with
        # the same unit as the input unit).
        ('Deposit temp.', layer.deposit_temp, DepositTempField),
        ('Nominal thickness', layer.nominal_thickness, NominalThicknessField),
        ('Shadow mask', layer.shadow_mask_description, ShadowMaskField),
        ('Function', layer.function, FilmLayerFunctionField),
        ('Nominal stoichio.', StoichioElement.to_str(layer.nominal_stoichio),
            NominalStoichioField),
    ]

    description_items = []
    for title, db_value, field in title_db_value_input_fields:
        if isinstance(field, UnitField):
            quantity_str = field.db_to_ui_str(db_value) if db_value is not None\
                else '_None_'
        else:
            quantity_str = db_value if db_value is not None else '_None_'
        description_items.append(f"**{title}:** {quantity_str}")
    st.write('\n\n'.join(description_items))

    st.divider()

    if layer.sputtering_system == SputteringSystem.MAGNETRON:
        st.subheader('Magnetron Sputtering')
        sputtering = layer.magnetron_sputterings[0]
    elif layer.sputtering_system == SputteringSystem.TRIODE:
        st.subheader('Triode Sputtering')
        sputtering = layer.triode_sputterings[0]
    else:
        raise RuntimeError

    st.write(sputtering.data_string())

    targets_used = (
        Target.select()
        .join(TargetUse, on=(Target.id == TargetUse.target))
        .join(FilmLayer, on=(FilmLayer.id == TargetUse.film_layer))
        .where(FilmLayer.id == layer)
    ).dicts()
    st.divider()
    st.subheader("Target(s) used:")
    for t in targets_used:
        target_label = t[Target.label.name]
        q_params = {IdType.TARGET: t['id']}
        switch_button(
            pages.inspect_target, label=target_label, q_params=q_params,
        )
