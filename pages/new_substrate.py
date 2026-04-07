from dataclasses import dataclass

from logic.constants import SessionKeys as Sk
from logic.db_schema import Substrate, db, SubstrateLayer
from logic.form_fields.new_substrate import StoichiometryField, CommentField, SubstrateNameField, ThicknessField, HField, \
    KField, LField
from logic.form_fields.shared import PopupData
from logic.functions import load_session_state
import streamlit as st


sess = load_session_state('new_substrate.py')


name_fld = SubstrateNameField.input()
comment_fld = CommentField.input()

if Sk.SUBSTRATE_LAYERS not in sess:
    sess[Sk.SUBSTRATE_LAYERS] = []
layers = sess[Sk.SUBSTRATE_LAYERS]

st.subheader("Layers:")

if len(layers) == 0:
    st.write('No layers yet.')

for layer_i, form in enumerate(layers):
    form: LayerData
    col1, col2 = st.columns([85, 15])
    with col1:
        # TODO put thickness unit:
        st.write(f"• {form.stoichio}\t|\t{form.thickness}\t|\t({form.h} {form.k} {form.l})")
    with col2:
        if st.button("❌", key=f"patch_{layer_i}"):
            layers.pop(layer_i)
            st.rerun()

# class LayerForm:
#     @st.dialog("New Layer")
#     def __init__(self):
#         sess_ = st.session_state
#         col1_, col2_ = st.columns(2)
#         with col1_:
#             stoichio_fld = StoichiometryField.input()
#         with col2_:
#             thickness_fld = ThicknessField.input()
#         col1_, col2_, col3_ = st.columns(3)
#         st.write(f"**Crystal Orientation**")
#         with col1_:
#             h_fld = HField.input()
#         with col2_:
#             k_fld = KField.input()
#         with col3_:
#             l_fld = LField.input()
#
#         fields_ = [stoichio_fld, thickness_fld, h_fld, k_fld, l_fld]
#         all_fields_valid = all([fld.is_valid for fld in fields_])
#
#         if st.button("Add Layer", disabled=not all_fields_valid):
#             for fld in fields_:
#                 fld.remove_from_session()  # To have a new one in the next pop-up.
#             self.stoichio = stoichio_fld.value
#             self.thickness = thickness_fld.value
#             self.h = h_fld.value
#             self.k = k_fld.value
#             self.l = l_fld.value
#             sess_[Sk.SUBSTRATE_LAYER_FORMS].append(self)
#             st.rerun()


@dataclass
class LayerData(PopupData):
    stoichio: str
    thickness: float
    h: int
    k: int
    l: int

    @classmethod
    @st.dialog("New Layer")
    def form_to_session(cls):
        col1_, col2_ = st.columns(2)
        with col1_:
            stoichio_fld = StoichiometryField.input()
        with col2_:
            thickness_fld = ThicknessField.input()
        col1_, col2_, col3_ = st.columns(3)
        st.write(f"**Crystal Orientation**")
        with col1_:
            h_fld = HField.input()
        with col2_:
            k_fld = KField.input()
        with col3_:
            l_fld = LField.input()

        fields_ = [stoichio_fld, thickness_fld, h_fld, k_fld, l_fld]
        all_fields_valid = all(fld.is_valid for fld in fields_)

        if st.button("Add Layer", disabled=not all_fields_valid):
            data_ = cls(
                fields_, stoichio_fld.value, thickness_fld.value, h_fld.value, k_fld.value, l_fld.value
            )
            data_.clear_and_add_to_session(session_key=Sk.SUBSTRATE_LAYERS)



if st.button("Add Layer"):
    LayerData.form_to_session()



all_fields = [name_fld, comment_fld]
can_submit = name_fld.is_valid and comment_fld.is_valid and len(sess[Sk.SUBSTRATE_LAYERS]) > 0

if st.button("Submit", disabled=not can_submit, type='primary'):
    substrate = Substrate.new(name=name_fld.value, comment=comment_fld.value)
    with db.atomic():
        substrate.save()
        for data in sess[Sk.SUBSTRATE_LAYERS]:
            data: LayerData
            layer = SubstrateLayer.new(data.thickness, data.h, data.k, data.l, data.stoichio, substrate)
            layer.save()
    st.switch_page('substrate_added.py')