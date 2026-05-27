from dataclasses import dataclass
from datetime import datetime

import streamlit as st

from pages import PageEnum
from logic.constants import SessionKeys as Sk, CookieKeys as Ck
from logic.db_enums import SputteringSystem, FilmLayerFunction, \
    MagnetronSputteringGenerator
from logic.lab_modelization.db_models import Target, FilmLayer, Film, db, Substrate, \
    MagnetronSputtering, TriodeSputtering, Library
from forms.new_library.fields import LibNameField, FilmPhysicalNameField, \
    CommentField, MadeOnField, MadeByField, \
    SputteringSystemField, TargetField, FilmLayerFunctionField, \
    StoichiometryField, \
    DepositDistanceField, DepositAngleField, SputteringGeneratorField, \
    HasActiveCoolingField, RotationField, \
    FilamentCurrentField, SubstrateField, DepositTempField, \
    DepositDurationField, DepositPowerField
from forms.shared import DialogData
from logic.functions import load_session_state, save_session_state

sess = load_session_state(PageEnum.new_lib)

st.title('New Library')

lib_name_fld = LibNameField.input()
target_fld = TargetField.input()
substrate_fld = SubstrateField.input()
film_name_fld = FilmPhysicalNameField.input()
comment_fld = CommentField.input()
made_on_fld = MadeOnField.input()
made_by_fld = MadeByField.input()
sputtering_sys_fld = SputteringSystemField.input()  # As supposed to be the
# same for all layers.
sess[Sk.SPUTTERING_SYSTEM] = sputtering_sys_fld.value

all_flds = [lib_name_fld, film_name_fld, comment_fld, made_on_fld, made_by_fld,
            sputtering_sys_fld, target_fld]

st.divider()

@dataclass
class LayerData(DialogData):
    deposit_temp: float
    deposit_duration: float
    deposit_power: float
    stoichio: str
    function: FilmLayerFunction
    sputtering: Magnetron | Triode

    @dataclass
    class Magnetron:
        deposit_distance: float
        deposit_angle: float
        sputtering_generator: MagnetronSputteringGenerator

    @dataclass
    class Triode:
        has_active_cooling: bool
        rotation: float
        filament_current: float

    @classmethod
    @st.dialog("Layer info")
    def form(cls):
        stoichio_fld = StoichiometryField.input()
        function_fld = FilmLayerFunctionField.input()
        deposit_temp = DepositTempField.input()
        deposit_duration = DepositDurationField.input()
        deposit_power = DepositPowerField.input()
        fields_ = [stoichio_fld, function_fld, deposit_temp, deposit_duration,
                   deposit_power]

        sputtering_sys = sess[Sk.SPUTTERING_SYSTEM]
        if sputtering_sys == SputteringSystem.MAGNETRON:
            deposit_distance_fld = DepositDistanceField.input()
            deposit_angle_fld = DepositAngleField.input()
            sputtering_gen_fld = SputteringGeneratorField.input()
            fields_ += [deposit_distance_fld, deposit_angle_fld,
                        sputtering_gen_fld]
            sputtering_data = cls.Magnetron(deposit_distance_fld.value,
                                            deposit_angle_fld.value,
                                            sputtering_gen_fld.value)
        elif sputtering_sys == SputteringSystem.TRIODE:
            active_cooling_fld = HasActiveCoolingField.input()
            rotation_fld = RotationField.input()
            filament_current_fld = FilamentCurrentField.input()
            fields_ += [active_cooling_fld, rotation_fld, filament_current_fld]
            sputtering_data = cls.Triode(active_cooling_fld.value,
                                         rotation_fld.value,
                                         filament_current_fld.value)
        else:
            raise RuntimeError(f"Unknown sputtering system: {sputtering_sys}.")

        if st.button('OK', disabled=not all(f.is_valid for f in fields_)):
            data_ = cls(
                fields_,
                deposit_temp.value,
                deposit_duration.value,
                deposit_power.value,
                stoichio_fld.value,
                function_fld.value,
                sputtering_data,
            )
            data_.clear_and_add_to_session(Sk.LAYER_DATA)


if Sk.LAYER_DATA not in sess:
    sess[Sk.LAYER_DATA] = []
layer_data_list: list[LayerData] = sess[Sk.LAYER_DATA]

base_fields_valid = all(f.is_valid for f in all_flds)

if base_fields_valid:
    st.subheader("Layers")
    st.write("**From buffer layer ⬇️**")
    for i, data in enumerate(layer_data_list):
        flex = st.container(horizontal=True, vertical_alignment='center')
        flex.write(f"Layer {i}: {data.stoichio}")
        if flex.button("❌", key=i):
            layer_data_list.pop(i)
            st.rerun()
    if st.button("Add layer", key='add_btn'):
        LayerData.form()
    st.write("**To capping layer ⬆️**")

    st.divider()

can_submit = base_fields_valid and len(layer_data_list) > 0

if st.button("Submit Library", disabled=not can_submit):
    target = Target.from_name(target_fld.value)
    substrate = Substrate.get(Substrate.name == substrate_fld.value)
    library = Library(lib_name_fld.value, datetime.now(), comment_fld.value)
    film = Film(film_name_fld.value, made_on_fld.value, made_by_fld.value,
                substrate,
                library)
    film_layers = [
        FilmLayer(
            position_from_buffer=i,
            deposit_temp=data.deposit_temp,
            deposit_duration=data.deposit_duration,
            deposit_power=data.deposit_power,
            stoichiometry=data.stoichio,
            function=data.function,
            film=film,
            target=target,
            sputtering_system=sputtering_sys_fld.value
        )
        for i, data in enumerate(layer_data_list)
    ]
    magnetron_sputterings = [
        MagnetronSputtering(
            deposit_distance=additional.sputtering.deposit_distance,
            deposit_angle=additional.sputtering.deposit_angle,
            generator=additional.sputtering.sputtering_generator,
            film_layer=film_layers[i],
        )
        for i, additional in enumerate(layer_data_list)
        if isinstance(additional.sputtering, LayerData.Magnetron)
    ]
    triode_sputterings = [
        TriodeSputtering(
            has_active_cooling=additional.sputtering.has_active_cooling,
            rotation=additional.sputtering.rotation,
            filament_current=additional.sputtering.filament_current,
            film_layer=film_layers[i],
        )
        for i, additional in enumerate(layer_data_list)
        if isinstance(additional.sputtering, LayerData.Triode)
    ]

    with db.atomic():
        target.save()
        substrate.save()
        library.save()
        film.save()
        for layer in film_layers:
            layer.save()
        for sputtering in magnetron_sputterings:
            sputtering.save()
        for sputtering in triode_sputterings:
            sputtering.save()

        sess[Ck.LAST_EMAIL_USED] = made_by_fld.value

    save_session_state(sess)
    st.switch_page('added_library.py')
