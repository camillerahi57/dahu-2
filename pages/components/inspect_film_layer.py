import streamlit as st

from components.browse import INSPECT_BUTTON_KEY
from components.streamlit_tools import sess, switch_button
from logic.constants import IdType
from logic.db_enums import SputteringSystem
from logic.lab_modelization.db_models import FilmLayer, Target, TargetUse
from logic.page_list import pages


@st.dialog(title="Layer info")
def show_film_layer(layers: list[FilmLayer]):
    """Show data about the layer that's been clicked on the layer table in
    the inspect library page."""
    layer = layers[sess[INSPECT_BUTTON_KEY]['row']]
    st.write(layer.data_string())

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
