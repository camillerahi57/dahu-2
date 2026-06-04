from logic.page_list import pages
from components.forms.new_substrate.sub_forms import RootForm
import streamlit as st

from logic.lab_modelization.db_models import db, Substrate, SubstrateLayer
from logic.functions import load_session_state, save_cookies

sess = load_session_state(pages.new_substrate)

root_form = RootForm()
substrate_name = root_form.substrate_name
comment = root_form.comment

layer_forms = root_form.layer_list_form.layer_forms
st.divider()

if root_form.is_valid:
    layer_strings = []
    for f in reversed(layer_forms):
        layer_strings.append(f'――――― {f.stoichio}')
    with st.container(border=True, width='content'):
        st.write("⬇️ Top layer")
        st.text('\n'.join(layer_strings))
        st.write("⬆️ Bottom layer")


if st.button("Submit", disabled=not root_form.is_valid, type='primary'):
    substrate = Substrate(name=substrate_name, comment=comment)
    with db.atomic():
        substrate.layers = []
        for i, form in enumerate(layer_forms):
            cryst_orient = form.cryst_orient_data
            h, k, l = cryst_orient.h, cryst_orient.k, cryst_orient.l
            layer = SubstrateLayer.from_stoichio(
                form.stoichio, form.thickness, h, k, l,
                substrate, position_from_back=i)
            substrate.layers.append(layer)
        substrate.save_with_dependent()

    save_cookies(sess)
    st.switch_page(pages.substrate_added)
