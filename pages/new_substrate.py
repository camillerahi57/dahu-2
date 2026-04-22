from dataclasses import dataclass

from logic.constants import SessionKeys as Sk
from logic.db_schema import Substrate, db, SubstrateLayer
from logic.form_fields.new_substrate import StoichiometryField, CommentField, \
    SubstrateNameField, ThicknessField, HField, \
    KField, LField, HasCrystalOrientationField
from logic.form_fields.shared import DialogData
from logic.functions import load_session_state, save_session_state
import streamlit as st

sess = load_session_state('new_substrate.py')

name_fld = SubstrateNameField.input()
comment_fld = CommentField.input()

if Sk.SUBSTRATE_LAYERS not in sess:
    sess[Sk.SUBSTRATE_LAYERS] = []
layers = sess[Sk.SUBSTRATE_LAYERS]

st.subheader("Layers:")
st.write("From back layer ⬇️")

if len(layers) == 0:
    st.write('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_No layers yet._')

for layer_i, form in enumerate(layers):
    form: LayerData
    col1, col2 = st.columns([85, 15])
    with col1:
        # TODO put thickness unit:
        to_write = f"- {form.stoichio}\t|\t{form.thickness}"
        if form.h is not None:
            to_write += f"\t|\t({form.h} {form.k} {form.l})"
        st.write(to_write)
    with col2:
        if st.button("❌", key=f"patch_{layer_i}"):
            layers.pop(layer_i)
            st.rerun()

st.write("To front layer ⬆️")


@dataclass
class LayerData(DialogData):
    stoichio: str
    thickness: float
    h: int|None
    k: int|None
    l: int|None

    @classmethod
    @st.dialog("New Layer")
    def form(cls):
        col1_, col2_ = st.columns(2)
        with col1_:
            stoichio_fld = StoichiometryField.input()
        with col2_:
            thickness_fld = ThicknessField.input()
        st.write(f"**Crystal Orientation**")
        has_orientation_fld = HasCrystalOrientationField.input()

        fields_ = [stoichio_fld, thickness_fld, has_orientation_fld]

        if has_orientation_fld.value is True:
            col1_, col2_, col3_ = st.columns(3)
            with col1_:
                h_fld = HField.input()
            with col2_:
                k_fld = KField.input()
            with col3_:
                l_fld = LField.input()
            fields_ += [h_fld, k_fld, l_fld]
            h, k, l = h_fld.value, k_fld.value, l_fld.value
            invalid_orientation = (h, k, l) == (0, 0, 0)
        else:
            h, k, l = None, None, None
            invalid_orientation = False

        all_fields_valid = all(fld.is_valid for fld in fields_)
        can_add = all_fields_valid and not invalid_orientation

        if st.button("Add Layer", disabled=not can_add):
            data_ = cls(
                fields_, stoichio_fld.value, thickness_fld.value, h, k, l
            )
            data_.clear_and_add_to_session(session_key=Sk.SUBSTRATE_LAYERS)


if st.button("Add Layer"):
    LayerData.form()

all_fields = [name_fld, comment_fld]
can_submit = name_fld.is_valid and comment_fld.is_valid and len(
    sess[Sk.SUBSTRATE_LAYERS]) > 0

if st.button("Submit", disabled=not can_submit, type='primary'):
    substrate = Substrate.new(name=name_fld.value, comment=comment_fld.value)
    with db.atomic():
        substrate.save()
        for i, data in enumerate(sess[Sk.SUBSTRATE_LAYERS]):
            data: LayerData
            layer = SubstrateLayer.new(data.thickness, data.h, data.k, data.l,
                                       data.stoichio, substrate, i)
            layer.save()
    save_session_state(sess)
    st.switch_page('substrate_added.py')
