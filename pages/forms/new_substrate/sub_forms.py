import streamlit as st

from forms.new_substrate.fields import HasCrystalOrientationField, HField, \
    KField, LField, StoichiometryField, ThicknessField, NbOfLayersField, \
    SubstrateNameField, CommentField
from forms.shared2 import Form


class CrystalOrientationForm(Form):
    def __init__(self, key: str):
        fields = []
        st.write(f"**Crystal Orientation**")
        with st.container(horizontal=True, vertical_alignment='top'):
            has_orientation_fld = HasCrystalOrientationField(key)
            fields.append(has_orientation_fld)
            if has_orientation_fld.value is True:
                col1_, col2_, col3_, col4_ = st.columns(4)
                with col2_:
                    h_fld = HField()
                with col3_:
                    k_fld = KField()
                with col4_:
                    l_fld = LField()
                h, k, l = h_fld.value, k_fld.value, l_fld.value
                fields.extend([h_fld, k_fld, l_fld])
            else:
                h, k, l = None, None, None

        self.has_orientation = has_orientation_fld.value
        self.h, self.k, self.l = h, k, l

        super().__init__(fields, [])

    def _check_coherence(self):
        if self.has_orientation:
            if (self.h, self.k, self.l) != (0, 0, 0):
                return True, ''
            else:
                return False, 'Invalid crystal orientation.'
        else:
            return True, ''


class LayerForm(Form):
    def __init__(self, key: str):
        with st.container(horizontal=True, vertical_alignment='center'):
            stoichio_fld = StoichiometryField(key)
            thickness_fld = ThicknessField(key)
        cryst_orient_form = CrystalOrientationForm(key)

        self.stoichio = stoichio_fld.value
        self.thickness = thickness_fld.value
        self.cryst_orient_form = cryst_orient_form

        super().__init__(
            [stoichio_fld, thickness_fld],
            [cryst_orient_form]
        )

    def _check_coherence(self):
        return True, ''


class LayerListForm(Form):
    def __init__(self):
        st.subheader("Layers:")

        nb_of_layers_fld = NbOfLayersField()
        st.divider()
        layer_nb = nb_of_layers_fld.value

        layer_forms = []
        if nb_of_layers_fld.is_valid:
            for i in range(layer_nb):
                if i == 0:
                    layer_label = 'Bottom layer'
                elif i == layer_nb - 1:
                    layer_label = 'Top layer'
                else:
                    layer_label = f"Layer {i+1}"
                with st.container(border=True):
                    st.subheader(layer_label)
                    layer_forms.append(LayerForm(key=str(i)))

        self.layer_forms = layer_forms
        super().__init__(
            [nb_of_layers_fld],
            layer_forms,
        )

    def _check_coherence(self):
        if len(self.layer_forms) == 0:
            return False, "Please add layer(s)."
        return True, ''


class RootForm(Form):
    def __init__(self):
        sub_name_fld = SubstrateNameField()
        comment_fld = CommentField()
        layer_list_form = LayerListForm()

        self.substrate_name = sub_name_fld.value
        self.comment = comment_fld.value
        self.layer_list_form = layer_list_form

        super().__init__(
            [sub_name_fld, comment_fld],
            [layer_list_form]
        )

    def _check_coherence(self):
        return True, ''