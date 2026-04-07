from dataclasses import dataclass
from datetime import datetime

from streamlit.runtime.uploaded_file_manager import UploadedFile

from logic.constants import SessionKeys as Sk, CookieKeys as Ck
from logic.db_schema import Target, FilmLayer, Film, db, Substrate, MagnetronSputtering, TriodeSputtering, Library, \
    UserUploadedFile
from logic.db_enums import SputteringSystem, FilmLayerFunction, MagnetronSputteringGenerator
from logic.form_fields.new_lib import LibNameField, FilmPhysicalNameField, CommentField, MadeOnField, MadeByField, \
    ZipUploadField, SputteringSystemField, TargetField, FilmLayerFunctionField, StoichiometryField, \
    DepositDistanceField, DepositAngleField, SputteringGeneratorField, HasActiveCoolingField, RotationField, \
    FilamentTensionField, SubstrateField

import streamlit as st

from logic.form_fields.shared import PopupData
from logic.functions import load_session_state, store_file, save_session_state

sess = load_session_state('new_lib.py')

st.title('New Library')

lib_name_fld = LibNameField.input()
target_fld = TargetField.input()
substrate_fld = SubstrateField.input()
film_name_fld = FilmPhysicalNameField.input()
comment_fld = CommentField.input()
made_on_fld = MadeOnField.input()
made_by_fld = MadeByField.input()
sputtering_sys_fld = SputteringSystemField.input()  # As supposed to be the same for all layers.
sess[Sk.SPUTTERING_SYSTEM] = sputtering_sys_fld.value
zip_upload_fld = ZipUploadField.input()

all_flds = [lib_name_fld, film_name_fld, comment_fld, made_on_fld, made_by_fld,
            sputtering_sys_fld, target_fld, zip_upload_fld]

@dataclass
class LayerZipData:
    position_from_buffer: int
    deposit_temp: float
    deposit_duration: float
    deposit_power: float
    thickness: float
    magnetron_deposit_distance: float|None = None
    magnetron_deposit_angle: float|None = None

fake_data = [LayerZipData(i, 42, 42, 42, 42) for i in range(2)]

zip_data_list: list[LayerZipData] = sorted(fake_data, key=lambda x: x.position_from_buffer)
assert [d.position_from_buffer for d in zip_data_list] == list(range(len(zip_data_list)))

st.divider()


@dataclass
class AdditionalLayerData(PopupData):
    stoichio: str
    function: FilmLayerFunction
    sputtering: Magnetron|Triode
    position_from_buffer: int

    @dataclass
    class Magnetron:
        deposit_distance: float
        deposit_angle: float
        sputtering_generator: MagnetronSputteringGenerator

    @dataclass
    class Triode:
        has_active_cooling: bool
        rotation: float
        filament_tension: float

    @classmethod
    @st.dialog("Layer info")
    def form_to_session(cls):
        stoichio_fld = StoichiometryField.input()
        function_fld = FilmLayerFunctionField.input()
        fields_ = [stoichio_fld, function_fld]

        sputtering_sys = sess[Sk.SPUTTERING_SYSTEM]

        if sputtering_sys == SputteringSystem.MAGNETRON:
            deposit_distance_fld = DepositDistanceField.input()
            deposit_angle_fld = DepositAngleField.input()
            sputtering_gen_fld = SputteringGeneratorField.input()
            fields_ += [deposit_distance_fld, deposit_angle_fld, sputtering_gen_fld]
            sputtering_data = cls.Magnetron(deposit_distance_fld.value, deposit_angle_fld.value,
                                            sputtering_gen_fld.value)
        elif sputtering_sys == SputteringSystem.TRIODE:
            active_cooling_fld = HasActiveCoolingField.input()
            rotation_fld = RotationField.input()
            filament_tension_fld = FilamentTensionField.input()
            fields_ += [active_cooling_fld, rotation_fld, filament_tension_fld]
            sputtering_data = cls.Triode(active_cooling_fld.value, rotation_fld.value,
                                         filament_tension_fld.value)
        else:
            raise RuntimeError(f"Unknown sputtering system {sputtering_sys}.")

        if st.button('OK', disabled=not all(f.is_valid for f in fields_)):
            position = sess[Sk.CURRENTLY_FILLED_LAYER_POSITION]
            data_ = cls(fields_, stoichio_fld.value, function_fld.value, sputtering_data,
                        position)
            data_.clear_and_add_to_session(Sk.ADDITIONAL_LAYER_DATA)

if Sk.ADDITIONAL_LAYER_DATA not in sess:
    sess[Sk.ADDITIONAL_LAYER_DATA] = []
additional_list: list[AdditionalLayerData] = sess[Sk.ADDITIONAL_LAYER_DATA]

base_fields_valid = all(f.is_valid for f in all_flds)

if base_fields_valid:
    st.subheader("Layers")
    st.write("**From buffer layer ⬇️**")
    for zip_data in zip_data_list:
        flex = st.container(horizontal=True, vertical_alignment='center')
        flex.write(f"Layer {zip_data.position_from_buffer + 1}")
        try:
            additional_data = next(d for d in additional_list
                                   if d.position_from_buffer == zip_data.position_from_buffer)
            flex.write(additional_data.stoichio)
            if flex.button("❌", key=zip_data.position_from_buffer):
                additional_list.remove(additional_data)
                st.rerun()
        except StopIteration:
            if flex.button("Fill Layer Info", key=zip_data.position_from_buffer):
                sess[Sk.CURRENTLY_FILLED_LAYER_POSITION] = zip_data.position_from_buffer
                AdditionalLayerData.form_to_session()
    st.write("**To capping layer ⬆️**")

    st.divider()

all_layers_filled = len(additional_list) == len(zip_data_list)
can_submit = base_fields_valid and all_layers_filled


if st.button("Submit Library", disabled=not can_submit):
    additional_list = sorted(additional_list, key=lambda d: d.position_from_buffer)

    target = Target.from_name(target_fld.value)
    substrate = Substrate.get(Substrate.name == substrate_fld.value)
    film = Film.new(film_name_fld.value, made_on_fld.value, made_by_fld.value, substrate)
    library = Library.new(lib_name_fld.value, datetime.now(), comment_fld.value, film)
    user_uploaded_file = UserUploadedFile.from_streamlit_uploaded_file(zip_upload_fld.value)
    film_layers = [
        FilmLayer.new(
            position_from_buffer=zip_.position_from_buffer,
            deposit_temp=zip_.deposit_temp,
            deposit_duration=zip_.deposit_duration,
            deposit_power=zip_.deposit_power,
            thickness=zip_.thickness,
            stoichiometry=additional.stoichio,
            function=additional.function,
            film=film,
            target=target,
            sputtering_system=sputtering_sys_fld.value
        )
        for zip_, additional in zip(zip_data_list, additional_list)
    ]
    magnetron_sputterings = [
        MagnetronSputtering.new(
            deposit_distance=additional.sputtering.deposit_distance,
            deposit_angle=additional.sputtering.deposit_angle,
            generator=additional.sputtering.sputtering_generator,
            film_layer=film_layers[i],
        )
        for i, additional in enumerate(additional_list)
        if isinstance(additional.sputtering, AdditionalLayerData.Magnetron)
    ]
    triode_sputterings = [
        TriodeSputtering.new(
            has_active_cooling=additional.sputtering.has_active_cooling,
            rotation=additional.sputtering.rotation,
            filament_tension=additional.sputtering.filament_tension,
            film_layer=film_layers[i],
        )
        for i, additional in enumerate(additional_list)
        if isinstance(additional.sputtering, AdditionalLayerData.Triode)
    ]


    with db.atomic():
        target.save()
        substrate.save()
        film.save()
        library.save()
        user_uploaded_file.save()
        for layer in film_layers:
            layer.save()
        for sputtering in magnetron_sputterings:
            sputtering.save()
        for sputtering in triode_sputterings:
            sputtering.save()

        uploaded_file_data: UploadedFile = zip_upload_fld.value
        store_file(uploaded_file_data.getvalue(), user_uploaded_file.file_name)
        sess[Ck.LAST_EMAIL_USED] = made_by_fld.value

    save_session_state(sess)
    st.switch_page('library_added.py')