import streamlit as st

from components.forms.base_classes import Form
from components.forms.new_substrate.fields import (
    HasCrystalOrientationField, HField, KField, LField, StoichiometryField,
    ThicknessField, LayerCountField, SubstrateLabelField, CommentField
)
from logic.lab_modelization.db_models import Substrate, SubstrateLayer, \
    StoichioElement


class CrystalOrientationForm(Form):
    def __init__(self, key: str, default_layer: SubstrateLayer|None):
        fields = []
        st.write(f"**Crystal Orientation**")
        with st.container(horizontal=True, vertical_alignment='top'):
            has_orientation_fld = HasCrystalOrientationField(
                key,
                form_default=None,
                db_default=default_layer.h is not None
                    if default_layer else None,
            )
            fields.append(has_orientation_fld)
            if has_orientation_fld.value is True:
                col1_, col2_, col3_, col4_ = st.columns(4)
                with col2_:
                    h_fld = HField(
                        key=f'h_{key}',
                        form_default=0,
                        db_default=default_layer.h if default_layer else None,
                    )
                with col3_:
                    k_fld = KField(
                        key=f'k_{key}',
                        form_default=0,
                        db_default=default_layer.k if default_layer else None,
                    )
                with col4_:
                    l_fld = LField(
                        key=f'l_{key}',
                        form_default=0,
                        db_default=default_layer.l if default_layer else None,
                    )
                h, k, l = h_fld.value, k_fld.value, l_fld.value
                fields.extend([h_fld, k_fld, l_fld])
            else:
                h, k, l = None, None, None

        self.has_orientation = has_orientation_fld.value
        self.h, self.k, self.l = h, k, l

        super().__init__(fields, [])

    def _is_coherent(self):
        if self.has_orientation:
            if (self.h, self.k, self.l) != (0, 0, 0):
                return True, ''
            else:
                return False, 'Invalid crystal orientation.'
        else:
            return True, ''


class LayerForm(Form):
    def __init__(self, key: str, default_layer: SubstrateLayer|None):
        with st.container(horizontal=True, vertical_alignment='center'):
            stoichio_fld = StoichiometryField(
                key,
                form_default=None,
                db_default=StoichioElement.to_str(default_layer.stoichio)
                    if default_layer else None,
            )
            thickness_fld = ThicknessField(
                key,
                form_default=0.,
                db_default=default_layer.thickness if default_layer else 0.,
            )
        cryst_orient_form = CrystalOrientationForm(key, default_layer)

        self.stoichio = stoichio_fld.value
        self.thickness = thickness_fld.in_db_unit
        self.cryst_orient_form = cryst_orient_form

        super().__init__(
            [stoichio_fld, thickness_fld],
            [cryst_orient_form]
        )

    def _is_coherent(self):
        return True, ''


class LayerListForm(Form):
    def __init__(self, default_sub: Substrate|None):
        st.subheader("Layers:")

        layer_count_fld = LayerCountField(
            form_default=0,
            db_default=len(default_sub.layers) if default_sub else None,
        )
        st.divider()
        layer_count = layer_count_fld.value

        layer_forms = []
        if layer_count_fld.is_valid:
            for i in range(layer_count):
                if i == 0:
                    layer_label = 'Bottom layer'
                elif i == layer_count - 1:
                    layer_label = 'Top layer'
                else:
                    layer_label = f"Layer {i+1}"
                with st.container(border=True):
                    st.subheader(layer_label)
                    try:
                        default_layer = default_sub.layers[i]
                    except IndexError, AttributeError:
                        default_layer = None
                    layer_form = LayerForm(
                        key=str(i),
                        default_layer=default_layer,
                    )
                    layer_forms.append(layer_form)

        self.layer_forms = layer_forms
        super().__init__(
            [layer_count_fld],
            layer_forms,
        )

    def _is_coherent(self):
        if len(self.layer_forms) == 0:
            return False, "Please add layer(s)."
        return True, ''


class RootForm(Form):
    def __init__(self, default_sub: Substrate|None):
        sub_label_fld = SubstrateLabelField(
            form_default=None,
            db_default=default_sub.label if default_sub else None,
        )
        comment_fld = CommentField(
            form_default=None,
            db_default=default_sub.comment if default_sub else None,
        )
        layer_list_form = LayerListForm(default_sub)

        self.substrate_name = sub_label_fld.value
        self.comment = comment_fld.value
        self.layer_list_form = layer_list_form

        super().__init__(
            [sub_label_fld, comment_fld],
            [layer_list_form]
        )

    def _is_coherent(self):
        return True, ''

    def show_layers(self):
        st.divider()
        layer_forms = self.layer_list_form.layer_forms
        if self.is_valid:
            layer_strings = []
            for f in reversed(layer_forms):
                layer_strings.append(f'――――――――――― {f.stoichio}')
            with st.container(border=True, width='content'):
                st.write("⬇️ Top layer")
                st.text('\n'.join(layer_strings))
                st.write("⬆️ Bottom layer")

    def to_substrate(self, id_: int = None) -> Substrate:
        substrate = Substrate(
            id=id_ if id_ is not None else None,
            label=self.substrate_name,
            comment=self.comment,
        )
        substrate.layers = []

        layer_forms = self.layer_list_form.layer_forms
        for i, form in enumerate(layer_forms):
            cryst_orient = form.cryst_orient_form
            h, k, l = cryst_orient.h, cryst_orient.k, cryst_orient.l
            layer = SubstrateLayer.from_stoichio(
                form.stoichio, form.thickness, h, k, l,
                substrate, position_from_back=i)
            substrate.layers.append(layer)

        return substrate